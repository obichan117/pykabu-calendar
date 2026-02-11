"""Matsui Securities earnings calendar source.

Uses requests (no browser needed).
"""

import logging
import re

import pandas as pd
from bs4 import BeautifulSoup

from ...core.fetch import fetch
from ...core.parse import parse_table, extract_regex, to_datetime, combine_datetime
from ..base import EarningsSource, load_config

logger = logging.getLogger(__name__)

_config = load_config(__file__)

# Module-level constants for backward compatibility
URL = _config["url"]
TABLE_SELECTOR = _config["table_selector"]
RESULT_SELECTOR = _config["result_selector"]
DATE_FORMAT = _config["date_format"]
NAME_CODE_COLUMN = _config["name_code_column"]
CODE_PATTERN = _config["code_pattern"]
NAME_PATTERN = _config["name_pattern"]
PER_PAGE = _config["per_page"]


def build_url(date: str, page: int = 1) -> str:
    """Build Matsui calendar URL.

    Args:
        date: Date in YYYY-MM-DD format
        page: Page number (1-indexed)

    Returns:
        Full URL with query parameters
    """
    year, month, day = date.split("-")
    return f"{URL}?date={year}/{int(month)}/{int(day)}&page={page}&per_page={PER_PAGE}"


def _parse(raw_df: pd.DataFrame, date: str) -> pd.DataFrame:
    """Parse raw Matsui DataFrame into standard format."""
    result = pd.DataFrame()

    if "発表日" in raw_df.columns:
        result["_date"] = to_datetime(raw_df["発表日"], format=DATE_FORMAT)
    else:
        result["_date"] = pd.to_datetime(date)

    if "発表時刻" in raw_df.columns:
        result["_time"] = raw_df["発表時刻"].replace("-", pd.NA)
    else:
        result["_time"] = pd.NA

    if NAME_CODE_COLUMN in raw_df.columns:
        col = raw_df[NAME_CODE_COLUMN]
        result["name"] = extract_regex(col, NAME_PATTERN)
        result["code"] = extract_regex(col, CODE_PATTERN)
    else:
        result["name"] = None
        result["code"] = None

    result["datetime"] = combine_datetime(result["_date"], result["_time"])

    return result[["code", "name", "datetime"]].dropna(subset=["code"])


class MatsuiEarningsSource(EarningsSource):
    """Matsui Securities earnings source (HTML scraping)."""

    _config = _config

    @property
    def name(self) -> str:
        return "matsui"

    def _fetch(self, date: str) -> pd.DataFrame:
        all_dfs = []
        page = 1

        while True:
            url = build_url(date, page=page)
            logger.debug(f"Fetching {url}")

            try:
                html = fetch(url)
            except Exception as e:
                logger.error(f"Matsui request failed: {e}")
                break

            soup = BeautifulSoup(html, "lxml")

            result_p = soup.select_one(RESULT_SELECTOR)
            if result_p and "0件中" in result_p.text:
                logger.info(f"No entries for {date}")
                break

            df = parse_table(html, TABLE_SELECTOR)
            if df.empty:
                break

            all_dfs.append(df)

            if result_p:
                match = re.search(r"(\d+)件中.*?(\d+)件", result_p.text)
                if match:
                    total, shown = int(match.group(1)), int(match.group(2))
                    if shown >= total:
                        break
                    page += 1
                else:
                    break
            else:
                break

        if not all_dfs:
            return pd.DataFrame(columns=["code", "name", "datetime"])

        raw_df = pd.concat(all_dfs, ignore_index=True)
        return _parse(raw_df, date)


# --- Backward-compat convenience function ---

_source = MatsuiEarningsSource()


def get_matsui(date: str) -> pd.DataFrame:
    """Get earnings calendar from Matsui Securities.

    Args:
        date: Target date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: [code, name, datetime]
    """
    return _source.fetch(date)
