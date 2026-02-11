"""Earnings calendar aggregator.

Merges calendar data from multiple sources to produce the most accurate
earnings datetime calendar.
"""

import logging

import pandas as pd

from .sources import SBIEarningsSource, MatsuiEarningsSource, TraderswebEarningsSource
from .inference import get_past_earnings, infer_datetime, is_during_trading_hours
from .ir import discover_ir_page, parse_earnings_datetime, get_cached, save_cache
from ..config import get_settings
from ..core.parallel import run_parallel
from ..llm import LLMClient

logger = logging.getLogger(__name__)

# Source instances (tuple to prevent accidental mutation)
ALL_SOURCES = (
    SBIEarningsSource(),
    MatsuiEarningsSource(),
    TraderswebEarningsSource(),
)

SCRAPERS = {src.name: src for src in ALL_SOURCES}

# Column order for output
OUTPUT_COLUMNS = [
    "code",
    "name",
    "datetime",
    "confidence",
    "during_trading_hours",
    "candidate_datetimes",
    "ir_datetime",
    "sbi_datetime",
    "matsui_datetime",
    "tradersweb_datetime",
    "inferred_datetime",
    "past_datetimes",
]


def get_calendar(
    date: str,
    sources: list[str] | None = None,
    infer_from_history: bool = True,
    include_ir: bool = True,
    ir_eager: bool = False,
    llm_client: LLMClient | None = None,
) -> pd.DataFrame:
    """Get aggregated earnings calendar for a target date.

    Args:
        date: Date in YYYY-MM-DD format
        sources: List of sources to use. Default: all sources (sbi, matsui, tradersweb).
        infer_from_history: Whether to infer time from historical patterns
        include_ir: Whether to include IR discovery (default True)
        ir_eager: Bypass IR cache and re-discover (default False)
        llm_client: Optional LLM client for IR discovery/parsing

    Returns:
        DataFrame with columns:
        - code: Stock code
        - name: Company name
        - datetime: Best estimate datetime
        - confidence: "highest", "high", "medium", or "low"
        - during_trading_hours: Whether datetime falls within TSE trading hours
        - candidate_datetimes: List of candidate datetimes (most likely first)
        - ir_datetime: Datetime from company IR page (if available)
        - sbi_datetime: Datetime from SBI (if available)
        - matsui_datetime: Datetime from Matsui (if available)
        - tradersweb_datetime: Datetime from Tradersweb (if available)
        - inferred_datetime: Datetime inferred from history
        - past_datetimes: List of past earnings datetimes
    """
    if sources is None:
        sources = list(SCRAPERS)

    logger.info(f"Getting calendar for {date} from sources: {sources}")

    # Fetch from all sources in parallel
    tasks = {}
    for source_name in sources:
        if source_name not in SCRAPERS:
            logger.warning(f"Unknown source: {source_name}")
            continue
        src = SCRAPERS[source_name]
        tasks[source_name] = lambda s=src: s.fetch(date)

    raw_results = run_parallel(tasks, max_workers=get_settings().max_workers)

    source_data = {}
    for name, df in raw_results.items():
        if not df.empty:
            source_data[name] = df
            logger.info(f"[{name}] Got {len(df)} entries")

    if not source_data:
        logger.warning("No data from any source")
        return _empty_result()

    # Merge all sources
    merged = _merge_sources(source_data)

    # Add historical data and inference
    merged = _add_history(merged, date, infer=infer_from_history)

    # Add IR discovery
    if include_ir:
        merged = _add_ir(merged, eager=ir_eager, llm_client=llm_client)

    # Build candidate list and select best datetime
    merged = _build_candidates(merged)

    # Add trading hours flag
    merged["during_trading_hours"] = merged["datetime"].apply(is_during_trading_hours)

    # Reorder columns
    return merged[[c for c in OUTPUT_COLUMNS if c in merged.columns]]


def check_sources() -> list[dict]:
    """Run health checks on all configured sources (in parallel).

    Returns:
        List of dicts with ``name``, ``ok``, ``rows``, ``error`` for each source.
    """
    sources = list(ALL_SOURCES)
    if not sources:
        return []
    tasks = {src.name: (lambda s=src: s.check()) for src in sources}
    results = run_parallel(tasks, max_workers=len(sources))
    return [results[src.name] for src in sources]


def _empty_result() -> pd.DataFrame:
    """Return empty DataFrame with correct schema and dtypes."""
    df = pd.DataFrame(columns=OUTPUT_COLUMNS)
    for col in df.columns:
        if col.endswith("_datetime") or col == "datetime":
            df[col] = pd.to_datetime(df[col])
    return df


def _merge_sources(source_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge DataFrames from multiple sources on stock code."""
    renamed = {}
    for source, df in source_data.items():
        df = df.copy()
        df = df.rename(columns={"datetime": f"{source}_datetime"})
        renamed[source] = df

    sources = list(renamed.keys())
    merged = renamed[sources[0]]

    for source in sources[1:]:
        df = renamed[source]
        merge_cols = ["code", f"{source}_datetime"]
        if "name" in df.columns and "name" not in merged.columns:
            merge_cols.append("name")
        df = df[[c for c in merge_cols if c in df.columns]]

        merged = pd.merge(merged, df, on="code", how="outer", suffixes=("", "_dup"))

        if "name_dup" in merged.columns:
            merged["name"] = merged["name"].fillna(merged["name_dup"])
            merged = merged.drop(columns=["name_dup"])

    # Enforce consistent dtypes after outer merge
    merged["code"] = merged["code"].astype(str)
    for col in merged.columns:
        if col.endswith("_datetime"):
            merged[col] = pd.to_datetime(merged[col], errors="coerce")

    return merged


def _add_history(df: pd.DataFrame, date: str, infer: bool = True) -> pd.DataFrame:
    """Add past_datetimes and optionally inferred_datetime columns."""
    settings = get_settings()

    def _fetch_history(code: str) -> tuple:
        past_dts = get_past_earnings(code)
        if infer:
            inferred_dt, _, _ = infer_datetime(code, date, past_datetimes=past_dts)
        else:
            inferred_dt = pd.NaT
        return past_dts if past_dts else None, inferred_dt

    tasks = {str(code): lambda c=str(code): _fetch_history(c) for code in df["code"]}
    results = run_parallel(tasks, max_workers=settings.max_workers)

    past_list = []
    inferred = []
    for code in df["code"]:
        code_str = str(code)
        if code_str in results:
            past_dts, inferred_dt = results[code_str]
            past_list.append(past_dts)
            inferred.append(inferred_dt)
        else:
            past_list.append(None)
            inferred.append(pd.NaT)

    df["inferred_datetime"] = pd.to_datetime(inferred, errors="coerce")
    df["past_datetimes"] = past_list

    return df


def _add_ir(
    df: pd.DataFrame,
    eager: bool = False,
    llm_client: LLMClient | None = None,
) -> pd.DataFrame:
    """Add ir_datetime column via IR page discovery and parsing."""
    settings = get_settings()

    tasks = {
        str(code): lambda c=str(code): _get_ir_datetime(
            c, eager=eager, llm_client=llm_client
        )
        for code in df["code"]
    }
    results = run_parallel(tasks, max_workers=settings.max_workers)

    ir_datetimes = []
    ir_found = 0
    for code in df["code"]:
        code_str = str(code)
        ir_dt = results.get(code_str, pd.NaT)
        ir_datetimes.append(ir_dt)
        if pd.notna(ir_dt):
            ir_found += 1

    df["ir_datetime"] = pd.to_datetime(ir_datetimes, errors="coerce")
    logger.info(f"[ir] Found {ir_found}/{len(df)} IR datetimes")

    return df


def _get_ir_datetime(
    code: str,
    eager: bool = False,
    llm_client: LLMClient | None = None,
) -> pd.Timestamp:
    """Get IR datetime for a single company."""
    if not eager:
        cached = get_cached(code)
        if cached and cached.last_earnings_datetime:
            try:
                return pd.Timestamp(cached.last_earnings_datetime)
            except (ValueError, TypeError):
                pass

    page_info = discover_ir_page(code, llm_client=llm_client)
    if not page_info:
        return pd.NaT

    earnings_info = parse_earnings_datetime(
        page_info.url,
        code=code,
        llm_client=llm_client,
    )
    if not earnings_info or not earnings_info.datetime:
        save_cache(
            code=code,
            ir_url=page_info.url,
            ir_type=page_info.page_type,
            discovered_via=page_info.discovered_via,
        )
        return pd.NaT

    save_cache(
        code=code,
        ir_url=page_info.url,
        ir_type=page_info.page_type,
        discovered_via=page_info.discovered_via,
        last_earnings_datetime=earnings_info.datetime,
    )

    return pd.Timestamp(earnings_info.datetime)


def _compute_confidence(
    ir_val: pd.Timestamp | None,
    inferred: pd.Timestamp | None,
    scrapers: dict[str, pd.Timestamp],
) -> str:
    """Compute confidence level based on source agreement.

    Returns:
        "highest" if IR data available, "high" if inferred matches scraper
        or 2+ scrapers agree, "medium" if multiple scrapers disagree,
        "low" if single source only.
    """
    if ir_val is not None and pd.notna(ir_val):
        return "highest"

    if inferred is not None and pd.notna(inferred) and scrapers:
        inferred_time = inferred.strftime("%H:%M")
        for val in scrapers.values():
            if val.strftime("%H:%M") == inferred_time:
                return "high"

    if len(scrapers) >= 2:
        times = [v.strftime("%H:%M") for v in scrapers.values()]
        if len(times) != len(set(times)):
            return "high"
        return "medium"

    return "low"


def _build_candidates(df: pd.DataFrame) -> pd.DataFrame:
    """Build candidate_datetimes list and select best datetime.

    Priority:
    1. ir_datetime (company IR page - most accurate)
    2. If inferred matches any source -> high confidence, use that
    3. If sources agree -> use that
    4. Otherwise -> inferred > sbi > matsui > tradersweb
    """
    datetime_cols = [
        "ir_datetime",
        "inferred_datetime",
        "sbi_datetime",
        "matsui_datetime",
        "tradersweb_datetime",
    ]
    available_cols = [c for c in datetime_cols if c in df.columns]

    scraper_cols = [c for c in available_cols if c not in ("ir_datetime", "inferred_datetime")]

    def build_row_candidates(row):
        """Build candidate list and select best datetime."""
        values = {}
        for col in available_cols:
            val = row.get(col)
            if pd.notna(val):
                values[col] = val

        if not values:
            return [], pd.NaT, "low"

        ir_val = values.get("ir_datetime")
        inferred = values.get("inferred_datetime")
        scrapers = {k: v for k, v in values.items() if k in scraper_cols}
        confidence = _compute_confidence(ir_val, inferred, scrapers)

        # Build ordered candidate list based on confidence
        candidates = []

        if ir_val is not None and pd.notna(ir_val):
            candidates.append(ir_val)
            for col in available_cols:
                if col != "ir_datetime" and col in values and values[col] not in candidates:
                    candidates.append(values[col])
            return candidates, candidates[0], confidence

        if confidence == "high" and inferred is not None and pd.notna(inferred) and scrapers:
            inferred_time = inferred.strftime("%H:%M")
            for val in scrapers.values():
                if val.strftime("%H:%M") == inferred_time:
                    candidates.append(inferred)
                    for other_val in scrapers.values():
                        if other_val not in candidates:
                            candidates.append(other_val)
                    return candidates, candidates[0], confidence

        if confidence == "high" and len(scrapers) >= 2:
            scraper_times = {col: v.strftime("%H:%M") for col, v in scrapers.items()}
            time_groups: dict[str, list] = {}
            for col, t in scraper_times.items():
                time_groups.setdefault(t, []).append(scrapers[col])
            largest_group = max(time_groups.values(), key=len)
            candidates.extend(largest_group)
            for v in values.values():
                if v not in candidates:
                    candidates.append(v)
            return candidates, candidates[0], confidence

        # No agreement — use priority order
        priority = ["inferred_datetime", "sbi_datetime", "matsui_datetime", "tradersweb_datetime"]
        for col in priority:
            if col in values:
                candidates.append(values[col])

        return candidates, candidates[0] if candidates else pd.NaT, confidence

    results = df.apply(build_row_candidates, axis=1)
    df["candidate_datetimes"] = results.apply(lambda x: x[0])
    df["datetime"] = pd.to_datetime(results.apply(lambda x: x[1]), errors="coerce")
    df["confidence"] = results.apply(lambda x: x[2])

    return df
