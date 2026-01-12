"""
Tradersweb earnings calendar scraper.

Uses requests (no browser needed).
"""

import logging

import pandas as pd

from ...core.fetch import fetch
from ...core.parse import parse_table, extract_regex, to_datetime, combine_datetime
from . import config

logger = logging.getLogger(__name__)


def get_tradersweb(date: str) -> pd.DataFrame:
    """
    Get earnings calendar from Tradersweb.

    Args:
        date: Target date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: [code, name, datetime]
    """
    url = config.build_url(date)
    logger.debug(f"Fetching {url}")

    try:
        html = fetch(url)
    except Exception as e:
        logger.error(f"Tradersweb request failed: {e}")
        return pd.DataFrame(columns=["code", "name", "datetime"])

    df = parse_table(html, config.TABLE_SELECTOR)
    if df.empty:
        logger.warning("Table not found or empty")
        return pd.DataFrame(columns=["code", "name", "datetime"])

    return _parse(df, date)


def _parse(raw_df: pd.DataFrame, date: str) -> pd.DataFrame:
    """Parse raw Tradersweb DataFrame into standard format."""
    result = pd.DataFrame()
    year = date.split("-")[0]

    # Parse date (format: "01/20" -> full date)
    if "発表日" in raw_df.columns:
        result["_date"] = to_datetime(
            year + "/" + raw_df["発表日"].astype(str),
            format=config.DATE_FORMAT,
        )
    else:
        result["_date"] = pd.to_datetime(date)

    # Parse time
    if "時刻" in raw_df.columns:
        result["_time"] = raw_df["時刻"].replace("-", pd.NA)
    else:
        result["_time"] = pd.NA

    # Find name column (contains "銘柄名")
    name_col = None
    for col in raw_df.columns:
        if config.NAME_COLUMN_PATTERN in col:
            name_col = col
            break

    if name_col:
        col_data = raw_df[name_col]
        result["name"] = extract_regex(col_data, config.NAME_PATTERN).str.strip()
        result["code"] = extract_regex(col_data, config.CODE_PATTERN)
    else:
        result["name"] = None
        result["code"] = None

    # Combine to datetime
    result["datetime"] = combine_datetime(result["_date"], result["_time"])

    # Filter out header rows
    result = result[result["code"].str.match(r"^\w+$", na=False)]

    return result[["code", "name", "datetime"]]
