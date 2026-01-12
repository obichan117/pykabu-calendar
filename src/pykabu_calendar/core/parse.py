"""
Generic parse utilities.

This module handles HTML/JSON parsing and data transformation.
It never imports requests/playwright - only takes raw input.
"""

import logging
import re
from io import StringIO
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_table(
    html: str,
    selector: Optional[str] = None,
    index: int = 0,
    **read_html_kwargs,
) -> pd.DataFrame:
    """
    Parse HTML table into DataFrame.

    Args:
        html: HTML content as string
        selector: CSS selector for table (optional, uses pd.read_html if None)
        index: Which table to return if multiple found
        **read_html_kwargs: Additional arguments for pd.read_html()

    Returns:
        DataFrame parsed from table
    """
    if selector:
        soup = BeautifulSoup(html, "lxml")
        table = soup.select_one(selector)
        if not table:
            logger.warning(f"Table not found with selector: {selector}")
            return pd.DataFrame()
        html = str(table)

    try:
        dfs = pd.read_html(StringIO(html), **read_html_kwargs)
        if not dfs:
            return pd.DataFrame()
        return dfs[index] if index < len(dfs) else dfs[0]
    except ValueError as e:
        logger.warning(f"Failed to parse table: {e}")
        return pd.DataFrame()


def extract_regex(series: pd.Series, pattern: str, group: int = 1) -> pd.Series:
    """
    Extract regex pattern from Series.

    Args:
        series: Pandas Series of strings
        pattern: Regex pattern with capture group
        group: Which capture group to extract (default: 1)

    Returns:
        Series with extracted values
    """
    return series.astype(str).str.extract(pattern, expand=False)


def to_datetime(
    series: pd.Series,
    format: Optional[str] = None,
    errors: str = "coerce",
) -> pd.Series:
    """
    Convert Series to datetime.

    Args:
        series: Series to convert
        format: datetime format string (optional)
        errors: How to handle errors ("coerce", "raise", "ignore")

    Returns:
        Series of datetime values
    """
    return pd.to_datetime(series, format=format, errors=errors)


def combine_datetime(
    date_series: pd.Series,
    time_series: pd.Series,
    default_time: str = "00:00",
) -> pd.Series:
    """
    Combine date and time series into datetime.

    Args:
        date_series: Series of dates
        time_series: Series of times (can have NaN)
        default_time: Default time for missing values

    Returns:
        Series of datetime values (NaT where time was unknown)
    """
    time_filled = time_series.fillna(default_time).astype(str)
    combined = pd.to_datetime(
        date_series.astype(str) + " " + time_filled,
        errors="coerce",
    )
    # Set to NaT where original time was unknown
    combined = combined.where(time_series.notna(), pd.NaT)
    return combined


def clean_text(series: pd.Series) -> pd.Series:
    """
    Clean text series (strip whitespace, normalize).

    Args:
        series: Series of strings

    Returns:
        Cleaned Series
    """
    return series.astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
