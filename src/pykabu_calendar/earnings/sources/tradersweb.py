"""Tradersweb earnings calendar source.

Uses requests (no browser needed).
"""

import logging

import pandas as pd
import requests

from ...core.fetch import fetch
from ...core.parse import parse_table, extract_regex, to_datetime, combine_datetime
from ..base import EarningsSource, load_config

logger = logging.getLogger(__name__)

_config = load_config(__file__)


def build_url(date: str) -> str:
    """Build Tradersweb calendar URL.

    Args:
        date: Date in YYYY-MM-DD format

    Returns:
        Full URL with query parameters
    """
    year, month, day = date.split("-")
    return f"{_config['url']}/all/all/1?term={year}/{month}/{day}"


def _parse(raw_df: pd.DataFrame, date: str) -> pd.DataFrame:
    """Parse raw Tradersweb DataFrame into standard format."""
    result = pd.DataFrame()
    year = date.split("-")[0]

    if "発表日" in raw_df.columns:
        result["_date"] = to_datetime(
            year + "/" + raw_df["発表日"].astype(str),
            format=_config["date_format"],
        )
    else:
        result["_date"] = pd.to_datetime(date)

    if "時刻" in raw_df.columns:
        result["_time"] = raw_df["時刻"].replace("-", pd.NA)
    else:
        result["_time"] = pd.NA

    name_col = None
    for col in raw_df.columns:
        if _config["name_column_pattern"] in col:
            name_col = col
            break

    if name_col:
        col_data = raw_df[name_col]
        result["name"] = extract_regex(col_data, _config["name_pattern"]).str.strip()
        result["code"] = extract_regex(col_data, _config["code_pattern"])
    else:
        result["name"] = None
        result["code"] = None

    result["datetime"] = combine_datetime(result["_date"], result["_time"])

    result = result[result["code"].str.match(r"^[0-9A-Z]{4}$", na=False)]

    return result[["code", "name", "datetime"]]


class TraderswebEarningsSource(EarningsSource):
    """Tradersweb earnings source (HTML scraping)."""

    _config = _config

    @property
    def name(self) -> str:
        return "tradersweb"

    def _fetch(self, date: str) -> pd.DataFrame:
        url = build_url(date)
        logger.debug(f"Fetching {url}")

        try:
            html = fetch(url)
        except requests.RequestException as e:
            logger.warning(f"Tradersweb request failed: {e}")
            return pd.DataFrame(columns=["code", "name", "datetime"])

        df = parse_table(html, _config["table_selector"])
        if df.empty:
            logger.warning("Table not found or empty")
            return pd.DataFrame(columns=["code", "name", "datetime"])

        return _parse(df, date)
