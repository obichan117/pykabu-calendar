"""
Earnings calendar aggregator.

Merges calendar data from multiple sources to produce the most accurate
earnings datetime calendar.
"""

import logging
from functools import reduce
from typing import Optional

import pandas as pd

from .sources import MatsuiCalendarScraper, SbiCalendarScraper, TraderswebCalendarScraper

logger = logging.getLogger(__name__)

# Source registry
AVAILABLE_SOURCES = {
    "sbi": SbiCalendarScraper,
    "matsui": MatsuiCalendarScraper,
    "tradersweb": TraderswebCalendarScraper,
}

# Default sources - SBI is primary, others are supplementary
DEFAULT_SOURCES = ["sbi", "matsui", "tradersweb"]


class EarningsCalendar:
    """
    Aggregates earnings calendar data from multiple sources.

    Priority for time selection:
    1. Official IR (if verify_official=True)
    2. Historical inference (if infer_from_history=True)
    3. SBI
    4. Matsui
    5. Tradersweb
    """

    def __init__(
        self,
        sources: list[str] = None,
        timeout: int = 60,
    ):
        """
        Initialize earnings calendar aggregator.

        Args:
            sources: List of source names to use. Defaults to all available.
            timeout: Request timeout in seconds.
        """
        self.sources = sources or DEFAULT_SOURCES
        self.timeout = timeout
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Initialize scrapers
        self._scrapers = {}
        for source in self.sources:
            if source in AVAILABLE_SOURCES:
                self._scrapers[source] = AVAILABLE_SOURCES[source](timeout=timeout)
            else:
                self.logger.warning(f"Unknown source: {source}")

    def get_calendar(
        self,
        target_date: str,
        infer_from_history: bool = True,
        verify_official: bool = False,
        eager: bool = False,
    ) -> pd.DataFrame:
        """
        Get aggregated earnings calendar for a target date.

        Args:
            target_date: Date in YYYY-MM-DD format
            infer_from_history: Whether to infer time from historical patterns
            verify_official: Whether to verify against company IR pages
            eager: If True, ignore cached IR data and re-fetch

        Returns:
            DataFrame with aggregated calendar data
        """
        self.logger.info(f"Getting calendar for {target_date}")

        # Fetch from all sources
        source_dfs = {}
        for name, scraper in self._scrapers.items():
            try:
                df = scraper.get_calendar(target_date)
                if not df.empty:
                    source_dfs[name] = df
                    self.logger.info(f"[{name}] Got {len(df)} entries")
            except Exception as e:
                self.logger.error(f"[{name}] Failed: {e}")

        if not source_dfs:
            self.logger.warning("No data from any source")
            return pd.DataFrame()

        # Merge all sources
        merged_df = self._merge_sources(source_dfs, target_date)

        # Add historical inference
        if infer_from_history:
            merged_df = self._add_historical_inference(merged_df)

        # Add official IR verification
        if verify_official:
            merged_df = self._add_official_verification(merged_df, eager=eager)

        # Select best time
        merged_df = self._select_best_time(merged_df)

        return merged_df

    def _merge_sources(
        self, source_dfs: dict[str, pd.DataFrame], target_date: str
    ) -> pd.DataFrame:
        """Merge DataFrames from multiple sources."""
        # Rename time column with source prefix
        renamed_dfs = []
        for source, df in source_dfs.items():
            df = df.copy()
            df = df.rename(columns={"time": f"time_{source}"})
            # Keep only needed columns
            cols = ["code", "date", f"time_{source}"]
            if "name" in df.columns:
                cols.append("name")
            if "type" in df.columns:
                cols.append("type")
            df = df[[c for c in cols if c in df.columns]]
            renamed_dfs.append(df)

        # Merge on code
        if len(renamed_dfs) == 1:
            merged = renamed_dfs[0]
        else:
            merged = reduce(
                lambda left, right: pd.merge(
                    left, right, on="code", how="outer", suffixes=("", "_dup")
                ),
                renamed_dfs,
            )

        # Consolidate duplicate columns (name, type, date)
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            for col in ["name", "date", "type"]:
                dup_cols = [c for c in merged.columns if c.startswith(f"{col}_dup") or c == col]
                if len(dup_cols) > 1:
                    # Take first non-null value
                    merged[col] = merged[dup_cols].bfill(axis=1).iloc[:, 0]
                    # Drop duplicates
                    merged = merged.drop(columns=[c for c in dup_cols if c != col])

        return merged

    def _add_historical_inference(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time_inferred column based on historical patterns."""
        from .inference.historical import add_historical_inference

        return add_historical_inference(df)

    def _add_official_verification(
        self, df: pd.DataFrame, eager: bool = False
    ) -> pd.DataFrame:
        """Add time_official column from company IR pages."""
        # TODO: Implement IR discovery
        # For now, just add empty column
        df["time_official"] = None
        df["ir_url"] = None
        df["publishes_time"] = None
        return df

    def _select_best_time(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Select the best time from available sources.

        Priority: official > inferred > sbi > matsui > tradersweb
        """
        time_cols = [
            "time_official",
            "time_inferred",
            "time_sbi",
            "time_matsui",
            "time_tradersweb",
        ]

        # Get columns that exist
        available_time_cols = [c for c in time_cols if c in df.columns]

        if not available_time_cols:
            df["time"] = None
            df["time_source"] = None
            return df

        # Select first non-null value in priority order
        def get_best_time(row):
            for col in available_time_cols:
                val = row.get(col)
                if pd.notna(val) and val not in [None, "", "NaN"]:
                    return val, col.replace("time_", "")
            return None, None

        results = df.apply(get_best_time, axis=1)
        df["time"] = results.apply(lambda x: x[0])
        df["time_source"] = results.apply(lambda x: x[1])

        # Create datetime column
        df["datetime"] = pd.to_datetime(
            df["date"].astype(str) + " " + df["time"].fillna("00:00"),
            errors="coerce",
        )

        # Reorder columns
        priority_cols = [
            "code",
            "name",
            "datetime",
            "date",
            "time",
            "time_source",
            "type",
        ]
        other_cols = [c for c in df.columns if c not in priority_cols]
        df = df[[c for c in priority_cols if c in df.columns] + other_cols]

        return df


def get_calendar(
    target_date: str,
    sources: list[str] = None,
    infer_from_history: bool = True,
    verify_official: bool = False,
    eager: bool = False,
) -> pd.DataFrame:
    """
    Get earnings calendar for a specific date.

    Args:
        target_date: Date in YYYY-MM-DD format
        sources: List of sources to use (default: ["sbi", "matsui", "tradersweb"])
        infer_from_history: Whether to infer time from historical patterns
        verify_official: Whether to verify against company IR pages
        eager: If True, ignore cached IR data

    Returns:
        DataFrame with earnings calendar data
    """
    calendar = EarningsCalendar(sources=sources)
    return calendar.get_calendar(
        target_date,
        infer_from_history=infer_from_history,
        verify_official=verify_official,
        eager=eager,
    )
