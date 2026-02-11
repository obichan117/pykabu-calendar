"""Matsui Securities earnings calendar source.

Uses requests (no browser needed).
"""

import logging
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ...core.fetch import fetch
from ...core.parse import HTML_PARSER, parse_table, extract_regex, to_datetime, combine_datetime
from ..base import EarningsSource, load_config

logger = logging.getLogger(__name__)

_config = load_config(__file__)


def build_url(date: str, page: int = 1) -> str:
    """Build Matsui calendar URL.

    Args:
        date: Date in YYYY-MM-DD format
        page: Page number (1-indexed)

    Returns:
        Full URL with query parameters
    """
    year, month, day = date.split("-")
    url = _config["url"]
    per_page = _config["per_page"]
    return f"{url}?date={year}/{int(month)}/{int(day)}&page={page}&per_page={per_page}"


def _parse(raw_df: pd.DataFrame, date: str) -> pd.DataFrame:
    """Parse raw Matsui DataFrame into standard format."""
    result = pd.DataFrame()

    if "発表日" in raw_df.columns:
        result["_date"] = to_datetime(raw_df["発表日"], format=_config["date_format"])
    else:
        result["_date"] = pd.to_datetime(date)

    if "発表時刻" in raw_df.columns:
        result["_time"] = raw_df["発表時刻"].replace("-", pd.NA)
    else:
        result["_time"] = pd.NA

    name_code_column = _config["name_code_column"]
    if name_code_column in raw_df.columns:
        col = raw_df[name_code_column]
        result["name"] = extract_regex(col, _config["name_pattern"])
        result["code"] = extract_regex(col, _config["code_pattern"])
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
            except requests.RequestException as e:
                logger.warning(f"Matsui request failed: {e}")
                break

            soup = BeautifulSoup(html, HTML_PARSER)

            result_p = soup.select_one(_config["result_selector"])
            if result_p and "0件中" in result_p.text:
                logger.info(f"No entries for {date}")
                break

            df = parse_table(html, _config["table_selector"])
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
