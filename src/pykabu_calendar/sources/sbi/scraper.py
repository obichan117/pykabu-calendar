"""
SBI Securities earnings calendar scraper.

Requires Playwright (browser automation) because SBI uses JavaScript rendering.
"""

import logging

import pandas as pd

from ...core.fetch import fetch_browser_with_pagination
from ...core.parse import parse_table, extract_regex, to_datetime, combine_datetime
from . import config

logger = logging.getLogger(__name__)


def get_sbi(date: str) -> pd.DataFrame:
    """
    Get earnings calendar from SBI Securities.

    Requires Playwright: pip install playwright && playwright install chromium

    Args:
        date: Target date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: [code, name, datetime]
    """
    url = config.build_url(date)
    logger.debug(f"Fetching {url}")

    try:
        html_pages = fetch_browser_with_pagination(
            url=url,
            table_selector=config.TABLE_SELECTOR,
            next_button_text=config.NEXT_BUTTON,
            view_all_text=config.VIEW_ALL_BUTTON,
        )
    except ImportError as e:
        logger.warning(str(e))
        return pd.DataFrame(columns=["code", "name", "datetime"])
    except Exception as e:
        logger.error(f"SBI scraping failed: {e}")
        return pd.DataFrame(columns=["code", "name", "datetime"])

    if not html_pages:
        return pd.DataFrame(columns=["code", "name", "datetime"])

    # Parse all pages
    all_dfs = []
    for html in html_pages:
        df = parse_table(html)
        if not df.empty:
            all_dfs.append(df)

    if not all_dfs:
        return pd.DataFrame(columns=["code", "name", "datetime"])

    raw_df = pd.concat(all_dfs, ignore_index=True)
    return _parse(raw_df, date)


def _parse(raw_df: pd.DataFrame, date: str) -> pd.DataFrame:
    """Parse raw SBI DataFrame into standard format."""
    result = pd.DataFrame()

    # Parse date
    if "発表日" in raw_df.columns:
        result["_date"] = to_datetime(raw_df["発表日"], format=config.DATE_FORMAT)
        result["_date"] = result["_date"].fillna(pd.to_datetime(date))
    else:
        result["_date"] = pd.to_datetime(date)

    # Find time column (may have space: "発表 時刻")
    time_col = None
    for col in raw_df.columns:
        if config.TIME_COLUMN_PATTERN in col:
            time_col = col
            break

    if time_col:
        result["_time"] = extract_regex(raw_df[time_col], config.TIME_PATTERN)
    else:
        result["_time"] = pd.NA

    # Find name column
    name_col = None
    for col in raw_df.columns:
        if config.NAME_COLUMN_PATTERN in col:
            name_col = col
            break

    if name_col:
        col_data = raw_df[name_col]
        result["name"] = extract_regex(col_data, config.NAME_PATTERN)
        result["code"] = extract_regex(col_data, config.CODE_PATTERN)
    else:
        result["name"] = None
        result["code"] = None

    # Combine to datetime
    result["datetime"] = combine_datetime(result["_date"], result["_time"])

    return result[["code", "name", "datetime"]].dropna(subset=["code"])
