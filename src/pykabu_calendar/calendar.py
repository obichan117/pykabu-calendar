"""
Earnings calendar aggregator.

Merges calendar data from multiple sources to produce the most accurate
earnings datetime calendar.
"""

import logging
from typing import Optional

import pandas as pd

from .scrapers import fetch_matsui, fetch_sbi, fetch_tradersweb
from .inference import get_past_earnings, infer_datetime

logger = logging.getLogger(__name__)

# Available scrapers
SCRAPERS = {
    "sbi": fetch_sbi,
    "matsui": fetch_matsui,
    "tradersweb": fetch_tradersweb,
}

DEFAULT_SOURCES = ["matsui", "tradersweb"]  # Lightweight by default


def get_calendar(
    date: str,
    sources: Optional[list[str]] = None,
    include_sbi: bool = False,
    infer_from_history: bool = True,
) -> pd.DataFrame:
    """
    Get aggregated earnings calendar for a target date.

    Args:
        date: Date in YYYY-MM-DD format
        sources: List of sources to use. Default: ["matsui", "tradersweb"]
        include_sbi: If True, include SBI (requires Playwright)
        infer_from_history: Whether to infer time from historical patterns

    Returns:
        DataFrame with columns:
        - code: Stock code
        - name: Company name
        - datetime: Best estimate datetime
        - candidate_datetimes: List of candidate datetimes (most likely first)
        - sbi_datetime: Datetime from SBI (if available)
        - matsui_datetime: Datetime from Matsui (if available)
        - tradersweb_datetime: Datetime from Tradersweb (if available)
        - inferred_datetime: Datetime inferred from history
        - past_datetimes: List of past earnings datetimes
    """
    if sources is None:
        sources = list(DEFAULT_SOURCES)
        if include_sbi:
            sources.insert(0, "sbi")

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

    # Add historical inference
    if infer_from_history:
        merged = _add_inference(merged, date)
    else:
        merged["inferred_datetime"] = pd.NaT
        merged["past_datetimes"] = None

    # Build candidate list and select best datetime
    merged = _build_candidates(merged)

    # Reorder columns
    cols = [
        "code",
        "name",
        "datetime",
        "candidate_datetimes",
        "sbi_datetime",
        "matsui_datetime",
        "tradersweb_datetime",
        "inferred_datetime",
        "past_datetimes",
    ]
    return merged[[c for c in cols if c in merged.columns]]


def _empty_result() -> pd.DataFrame:
    """Return empty DataFrame with correct schema."""
    return pd.DataFrame(
        columns=[
            "code",
            "name",
            "datetime",
            "candidate_datetimes",
            "sbi_datetime",
            "matsui_datetime",
            "tradersweb_datetime",
            "inferred_datetime",
            "past_datetimes",
        ]
    )


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


def _add_inference(df: pd.DataFrame, date: str) -> pd.DataFrame:
    """Add inferred_datetime and past_datetimes columns."""
    inferred = []
    past_list = []

    for code in df["code"]:
        try:
            inferred_dt, confidence, past_dts = infer_datetime(str(code), date)
            inferred.append(inferred_dt)
            past_list.append(past_dts if past_dts else None)
        except Exception as e:
            logger.warning(f"Inference failed for {code}: {e}")
            inferred.append(pd.NaT)
            past_list.append(None)

    df["inferred_datetime"] = inferred
    df["past_datetimes"] = past_list

    return df


def _build_candidates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build candidate_datetimes list and select best datetime.

    Priority:
    1. If inferred matches any source -> high confidence, use that
    2. If sources agree -> use that
    3. Otherwise -> use inferred > sbi > matsui > tradersweb
    """
    datetime_cols = [
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

        # Check if inferred matches any source (high confidence)
        inferred = values.get("inferred_datetime")
        source_values = {k: v for k, v in values.items() if k != "inferred_datetime"}

        if inferred and source_values:
            # Compare times (ignore date differences)
            inferred_time = inferred.strftime("%H:%M") if pd.notna(inferred) else None
            for col, val in source_values.items():
                val_time = val.strftime("%H:%M") if pd.notna(val) else None
                if inferred_time == val_time:
                    # Inferred matches source - high confidence
                    candidates.append(inferred)
                    # Add other sources
                    for other_col, other_val in source_values.items():
                        if other_col != col and other_val not in candidates:
                            candidates.append(other_val)
                    return candidates, candidates[0] if candidates else pd.NaT

        # No match - use priority order
        priority = ["inferred_datetime", "sbi_datetime", "matsui_datetime", "tradersweb_datetime"]
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
