"""
Matsui Securities earnings calendar scraper.

Simple requests-based scraper - no browser needed.
"""

import logging
import re
from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup

from .config import TIMEOUT, build_matsui_url, get_session

logger = logging.getLogger(__name__)


def fetch_matsui(date: str, timeout: int = TIMEOUT) -> pd.DataFrame:
    """
    Fetch earnings calendar from Matsui Securities.

    Args:
        date: Target date in YYYY-MM-DD format
        timeout: Request timeout in seconds

    Returns:
        DataFrame with columns: [code, name, datetime]
    """
    session = get_session()
    all_rows = []
    page = 1

    while True:
        url = build_matsui_url(date, page=page)
        logger.debug(f"Fetching {url}")

        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
        except Exception as e:
            logger.error(f"Matsui request failed: {e}")
            break

        soup = BeautifulSoup(response.text, "lxml")

        # Check result count: "検索結果 N件中 X - Y件"
        result_p = soup.select_one("p.m-table-utils-result")
        if result_p and "0件中" in result_p.text:
            logger.info(f"No entries for {date}")
            break

        # Find data table
        table = soup.find("table", class_="m-table")
        if not table:
            logger.warning("Table not found")
            break

        # Parse table
        df = pd.read_html(StringIO(str(table)))[0]
        if df.empty:
            break

        all_rows.append(df)

        # Check pagination
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

    if not all_rows:
        return pd.DataFrame(columns=["code", "name", "datetime"])

    raw_df = pd.concat(all_rows, ignore_index=True)
    return _parse_matsui(raw_df, date)


def _parse_matsui(raw_df: pd.DataFrame, date: str) -> pd.DataFrame:
    """Parse raw Matsui DataFrame into standard format."""
    result = pd.DataFrame()

    # Parse date
    if "発表日" in raw_df.columns:
        result["_date"] = pd.to_datetime(raw_df["発表日"], format="%Y/%m/%d", errors="coerce")
    else:
        result["_date"] = pd.to_datetime(date)

    # Parse time
    if "発表時刻" in raw_df.columns:
        result["_time"] = raw_df["発表時刻"].replace("-", pd.NA)
    else:
        result["_time"] = pd.NA

    # Parse name and code from "銘柄名(銘柄コード)"
    name_col = "銘柄名(銘柄コード)"
    if name_col in raw_df.columns:
        result["name"] = raw_df[name_col].str.extract(r"^(.+?)\(")[0]
        result["code"] = raw_df[name_col].str.extract(r"\((\w+)\)")[0]
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

    return result[["code", "name", "datetime"]].dropna(subset=["code"])
