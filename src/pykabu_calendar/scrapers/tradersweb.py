"""
Tradersweb earnings calendar scraper.

Simple requests-based scraper - no browser needed.
"""

import logging
from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup

from .config import TIMEOUT, build_tradersweb_url, get_session

logger = logging.getLogger(__name__)


def fetch_tradersweb(date: str, timeout: int = TIMEOUT) -> pd.DataFrame:
    """
    Fetch earnings calendar from Tradersweb.

    Args:
        date: Target date in YYYY-MM-DD format
        timeout: Request timeout in seconds

    Returns:
        DataFrame with columns: [code, name, datetime]
    """
    session = get_session()
    url = build_tradersweb_url(date)
    logger.debug(f"Fetching {url}")

    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except Exception as e:
        logger.error(f"Tradersweb request failed: {e}")
        return pd.DataFrame(columns=["code", "name", "datetime"])

    soup = BeautifulSoup(response.text, "lxml")

    # Find data table
    table = soup.find("table", class_="data_table")
    if not table:
        logger.warning("Table not found")
        return pd.DataFrame(columns=["code", "name", "datetime"])

    try:
        df = pd.read_html(StringIO(str(table)))[0]
    except ValueError as e:
        logger.warning(f"Failed to parse table: {e}")
        return pd.DataFrame(columns=["code", "name", "datetime"])

    if df.empty:
        return pd.DataFrame(columns=["code", "name", "datetime"])

    return _parse_tradersweb(df, date)


def _parse_tradersweb(raw_df: pd.DataFrame, date: str) -> pd.DataFrame:
    """Parse raw Tradersweb DataFrame into standard format."""
    result = pd.DataFrame()
    year = date.split("-")[0]

    # Parse date (format: "01/20" -> full date)
    if "発表日" in raw_df.columns:
        result["_date"] = pd.to_datetime(
            year + "/" + raw_df["発表日"].astype(str),
            format="%Y/%m/%d",
            errors="coerce",
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
        if "銘柄名" in col:
            name_col = col
            break

    if name_col:
        # Format: "トヨタ自動車  (7203/東P)"
        result["name"] = raw_df[name_col].str.extract(r"^([^(]+)")[0].str.strip()
        result["code"] = raw_df[name_col].str.extract(r"\((\w+)/")[0]
    else:
        result["name"] = None
        result["code"] = None

    # Combine date and time into datetime
    result["datetime"] = pd.to_datetime(
        result["_date"].astype(str) + " " + result["_time"].fillna("00:00").astype(str),
        errors="coerce",
    )

    # Set datetime to None where time was unknown
    result.loc[result["_time"].isna(), "datetime"] = pd.NaT

    # Filter out header rows
    result = result[result["code"].str.match(r"^\w+$", na=False)]

    return result[["code", "name", "datetime"]]
