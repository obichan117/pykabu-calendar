"""
Earnings calendar aggregator.

Merges calendar data from multiple sources to produce the most accurate
earnings datetime calendar.
"""

import logging
from typing import Optional

import pandas as pd

from .sources import get_matsui, get_sbi, get_tradersweb
from .inference import get_past_earnings, infer_datetime
from .ir import discover_ir_page, parse_earnings_datetime, get_cached, save_cache
from .llm import LLMClient

logger = logging.getLogger(__name__)

# Available scrapers
SCRAPERS = {
    "sbi": get_sbi,
    "matsui": get_matsui,
    "tradersweb": get_tradersweb,
}

DEFAULT_SOURCES = ["sbi", "matsui", "tradersweb"]  # All sources by default

# Column order for output
OUTPUT_COLUMNS = [
    "code",
    "name",
    "datetime",
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
    sources: Optional[list[str]] = None,
    infer_from_history: bool = True,
    include_ir: bool = True,
    ir_eager: bool = False,
    llm_client: LLMClient | None = None,
) -> pd.DataFrame:
    """
    Get aggregated earnings calendar for a target date.

    Args:
        date: Date in YYYY-MM-DD format
        sources: List of sources to use. Default: all sources (sbi, matsui, tradersweb).
                 Note: SBI requires Playwright and may be slower than other sources.
        infer_from_history: Whether to infer time from historical patterns
        include_ir: Whether to include IR discovery (default True)
        ir_eager: Bypass IR cache and re-discover (default False)
        llm_client: Optional LLM client for IR discovery/parsing

    Returns:
        DataFrame with columns:
        - code: Stock code
        - name: Company name
        - datetime: Best estimate datetime
        - candidate_datetimes: List of candidate datetimes (most likely first)
        - ir_datetime: Datetime from company IR page (if available)
        - sbi_datetime: Datetime from SBI (if available)
        - matsui_datetime: Datetime from Matsui (if available)
        - tradersweb_datetime: Datetime from Tradersweb (if available)
        - inferred_datetime: Datetime inferred from history
        - past_datetimes: List of past earnings datetimes
    """
    if sources is None:
        sources = list(DEFAULT_SOURCES)

    logger.info(f"Getting calendar for {date} from sources: {sources}")

    # Fetch from all sources
    source_data = {}
    for source in sources:
        if source not in SCRAPERS:
            logger.warning(f"Unknown source: {source}")
            continue
        try:
            df = SCRAPERS[source](date)
            if not df.empty:
                source_data[source] = df
                logger.info(f"[{source}] Got {len(df)} entries")
        except Exception as e:
            logger.error(f"[{source}] Failed: {e}")

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

    # Reorder columns
    return merged[[c for c in OUTPUT_COLUMNS if c in merged.columns]]


def _empty_result() -> pd.DataFrame:
    """Return empty DataFrame with correct schema."""
    return pd.DataFrame(columns=OUTPUT_COLUMNS)


def _merge_sources(source_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge DataFrames from multiple sources on stock code."""
    # Rename datetime column with source prefix
    renamed = {}
    for source, df in source_data.items():
        df = df.copy()
        df = df.rename(columns={"datetime": f"{source}_datetime"})
        renamed[source] = df

    # Start with first source
    sources = list(renamed.keys())
    merged = renamed[sources[0]]

    # Merge remaining sources
    for source in sources[1:]:
        df = renamed[source]
        # Keep only code and datetime columns for merge
        merge_cols = ["code", f"{source}_datetime"]
        if "name" in df.columns and "name" not in merged.columns:
            merge_cols.append("name")
        df = df[[c for c in merge_cols if c in df.columns]]

        merged = pd.merge(merged, df, on="code", how="outer", suffixes=("", "_dup"))

        # Consolidate name column
        if "name_dup" in merged.columns:
            merged["name"] = merged["name"].fillna(merged["name_dup"])
            merged = merged.drop(columns=["name_dup"])

    return merged


def _add_history(df: pd.DataFrame, date: str, infer: bool = True) -> pd.DataFrame:
    """Add past_datetimes and optionally inferred_datetime columns."""
    inferred = []
    past_list = []

    for code in df["code"]:
        try:
            # Always get past earnings
            past_dts = get_past_earnings(str(code))
            past_list.append(past_dts if past_dts else None)

            # Only infer if requested
            if infer:
                inferred_dt, confidence, _ = infer_datetime(str(code), date)
                inferred.append(inferred_dt)
            else:
                inferred.append(pd.NaT)
        except Exception as e:
            logger.warning(f"History lookup failed for {code}: {e}")
            inferred.append(pd.NaT)
            past_list.append(None)

    df["inferred_datetime"] = inferred
    df["past_datetimes"] = past_list

    return df


def _add_ir(
    df: pd.DataFrame,
    eager: bool = False,
    llm_client: LLMClient | None = None,
) -> pd.DataFrame:
    """Add ir_datetime column via IR page discovery and parsing.

    Args:
        df: Merged DataFrame with code column
        eager: If True, bypass cache and re-discover
        llm_client: Optional LLM client for discovery/parsing
    """
    ir_datetimes = []
    ir_found = 0

    for code in df["code"]:
        code_str = str(code)
        try:
            ir_dt = _get_ir_datetime(code_str, eager=eager, llm_client=llm_client)
            ir_datetimes.append(ir_dt)
            if ir_dt is not pd.NaT:
                ir_found += 1
        except Exception as e:
            logger.warning(f"[ir] Failed for {code_str}: {e}")
            ir_datetimes.append(pd.NaT)

    df["ir_datetime"] = ir_datetimes
    logger.info(f"[ir] Found {ir_found}/{len(df)} IR datetimes")

    return df


def _get_ir_datetime(
    code: str,
    eager: bool = False,
    llm_client: LLMClient | None = None,
) -> pd.Timestamp:
    """Get IR datetime for a single company.

    Checks cache first, then discovers and parses IR page.
    """
    # Check cache first (unless eager mode)
    if not eager:
        cached = get_cached(code)
        if cached and cached.last_earnings_datetime:
            try:
                return pd.Timestamp(cached.last_earnings_datetime)
            except (ValueError, TypeError):
                pass

    # Discover IR page
    page_info = discover_ir_page(code, llm_client=llm_client)
    if not page_info:
        return pd.NaT

    # Parse earnings datetime from the IR page
    earnings_info = parse_earnings_datetime(
        page_info.url,
        code=code,
        llm_client=llm_client,
    )
    if not earnings_info or not earnings_info.datetime:
        # Cache the page URL even without datetime (for future use)
        save_cache(
            code=code,
            ir_url=page_info.url,
            ir_type=page_info.page_type,
            discovered_via=page_info.discovered_via,
        )
        return pd.NaT

    # Cache successful result
    save_cache(
        code=code,
        ir_url=page_info.url,
        ir_type=page_info.page_type,
        discovered_via=page_info.discovered_via,
        last_earnings_datetime=earnings_info.datetime,
    )

    return pd.Timestamp(earnings_info.datetime)


def _build_candidates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build candidate_datetimes list and select best datetime.

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

    def build_row_candidates(row):
        """Build candidate list for a single row."""
        candidates = []
        values = {}

        for col in available_cols:
            val = row.get(col)
            if pd.notna(val):
                values[col] = val

        if not values:
            return [], pd.NaT

        # IR datetime is highest priority (official source)
        ir_val = values.get("ir_datetime")
        if ir_val:
            candidates.append(ir_val)
            for col in available_cols:
                if col != "ir_datetime" and col in values and values[col] not in candidates:
                    candidates.append(values[col])
            return candidates, candidates[0]

        # Check if inferred matches any source (high confidence)
        inferred = values.get("inferred_datetime")
        source_values = {
            k: v for k, v in values.items()
            if k not in ("inferred_datetime", "ir_datetime")
        }

        if inferred and source_values:
            # Compare times (ignore date differences)
            inferred_time = inferred.strftime("%H:%M") if pd.notna(inferred) else None
            for col, val in source_values.items():
                val_time = val.strftime("%H:%M") if pd.notna(val) else None
                if inferred_time == val_time:
                    # Inferred matches source - high confidence
                    candidates.append(inferred)
                    for other_col, other_val in source_values.items():
                        if other_col != col and other_val not in candidates:
                            candidates.append(other_val)
                    return candidates, candidates[0] if candidates else pd.NaT

        # No match - use priority order
        priority = [
            "inferred_datetime",
            "sbi_datetime",
            "matsui_datetime",
            "tradersweb_datetime",
        ]
        for col in priority:
            if col in values:
                candidates.append(values[col])

        return candidates, candidates[0] if candidates else pd.NaT

    results = df.apply(build_row_candidates, axis=1)
    df["candidate_datetimes"] = results.apply(lambda x: x[0])
    df["datetime"] = results.apply(lambda x: x[1])

    return df


# Convenience function for CSV export
def export_to_csv(df: pd.DataFrame, path: str) -> None:
    """
    Export calendar to CSV with proper encoding for Excel/Google Sheets.

    Args:
        df: Calendar DataFrame
        path: Output file path
    """
    # Convert list columns to string representation
    export_df = df.copy()

    for col in ["candidate_datetimes", "past_datetimes"]:
        if col in export_df.columns:
            export_df[col] = export_df[col].apply(
                lambda x: "; ".join(str(v) for v in x) if isinstance(x, list) else ""
            )

    export_df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"Exported {len(df)} entries to {path}")
