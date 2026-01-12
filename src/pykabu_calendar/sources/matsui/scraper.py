"""
Matsui Securities earnings calendar scraper.

Uses requests (no browser needed).
"""

import logging
import re

import pandas as pd
from bs4 import BeautifulSoup

from ...core.fetch import fetch
from ...core.parse import parse_table, extract_regex, to_datetime, combine_datetime
from . import config

logger = logging.getLogger(__name__)


def get_matsui(date: str) -> pd.DataFrame:
    """
    Get earnings calendar from Matsui Securities.

    Args:
        date: Target date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: [code, name, datetime]
    """
    all_dfs = []
    page = 1

    while True:
        url = config.build_url(date, page=page)
        logger.debug(f"Fetching {url}")

        try:
            html = fetch(url)
        except Exception as e:
            logger.error(f"Matsui request failed: {e}")
            break

        soup = BeautifulSoup(html, "lxml")

        # Check result count
        result_p = soup.select_one(config.RESULT_SELECTOR)
        if result_p and "0件中" in result_p.text:
            logger.info(f"No entries for {date}")
            break

        # Parse table
        df = parse_table(html, config.TABLE_SELECTOR)
        if df.empty:
            break

        all_dfs.append(df)

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

    if not all_dfs:
        return pd.DataFrame(columns=["code", "name", "datetime"])

    raw_df = pd.concat(all_dfs, ignore_index=True)
    return _parse(raw_df, date)


def _parse(raw_df: pd.DataFrame, date: str) -> pd.DataFrame:
    """Parse raw Matsui DataFrame into standard format."""
    result = pd.DataFrame()

    # Parse date
    if "発表日" in raw_df.columns:
        result["_date"] = to_datetime(raw_df["発表日"], format=config.DATE_FORMAT)
    else:
        result["_date"] = pd.to_datetime(date)

    # Parse time
    if "発表時刻" in raw_df.columns:
        result["_time"] = raw_df["発表時刻"].replace("-", pd.NA)
    else:
        result["_time"] = pd.NA

    # Parse name and code
    if config.NAME_CODE_COLUMN in raw_df.columns:
        col = raw_df[config.NAME_CODE_COLUMN]
        result["name"] = extract_regex(col, config.NAME_PATTERN)
        result["code"] = extract_regex(col, config.CODE_PATTERN)
    else:
        result["name"] = None
        result["code"] = None

    # Combine to datetime
    result["datetime"] = combine_datetime(result["_date"], result["_time"])

    return result[["code", "name", "datetime"]].dropna(subset=["code"])
