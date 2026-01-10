"""
Matsui Securities earnings calendar scraper.

Matsui provides calendar data via their finance.matsui.co.jp site.
Works with plain requests - no browser automation needed.
"""

import logging
from io import StringIO
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup

from .base import BaseCalendarScraper, SourceUnavailableError

logger = logging.getLogger(__name__)


class MatsuiCalendarScraper(BaseCalendarScraper):
    """Scraper for Matsui Securities earnings calendar."""

    BASE_URL = "https://finance.matsui.co.jp/find-by-schedule/index"
    PER_PAGE = 100

    @property
    def name(self) -> str:
        return "matsui"

    def _try_scrape(self, target_date: str) -> Optional[pd.DataFrame]:
        """Scrape Matsui calendar via requests."""
        year, month, day = target_date.split("-")
        date_param = f"{year}/{int(month)}/{int(day)}"

        all_dfs = []
        page = 1

        while True:
            url = f"{self.BASE_URL}?date={date_param}&page={page}&per_page={self.PER_PAGE}"
            self.logger.debug(f"Fetching {url}")

            try:
                response = self._request(url)
            except SourceUnavailableError as e:
                self.logger.error(f"Failed to fetch Matsui: {e}")
                return None

            soup = BeautifulSoup(response.text, "lxml")

            # Check result count
            result_p = soup.select_one("p.m-table-utils-result")
            if result_p:
                result_text = result_p.text
                # Format: "検索結果 N件中 X - Y件"
                if "0件中" in result_text:
                    self.logger.info(f"No entries for {target_date}")
                    return pd.DataFrame(columns=self.OUTPUT_COLUMNS)

            # Find the data table
            table = soup.find("table", class_="m-table")
            if not table:
                self.logger.warning("Table not found on Matsui page")
                return None

            # Parse table
            df = pd.read_html(StringIO(str(table)))[0]
            if df.empty:
                break

            all_dfs.append(df)

            # Check if there are more pages
            # Result format: "検索結果 284件中 1 - 100件"
            if result_p:
                import re

                match = re.search(r"(\d+)件中.*?(\d+)件", result_text)
                if match:
                    total = int(match.group(1))
                    shown = int(match.group(2))
                    if shown >= total:
                        break
                    page += 1
                else:
                    break
            else:
                break

        if not all_dfs:
            return pd.DataFrame(columns=self.OUTPUT_COLUMNS)

        # Combine all pages
        raw_df = pd.concat(all_dfs, ignore_index=True)
        return self._parse_dataframe(raw_df, target_date)

    def _parse_dataframe(self, raw_df: pd.DataFrame, target_date: str) -> pd.DataFrame:
        """Parse raw Matsui DataFrame into standard format."""
        # Expected columns: ['発表日', '発表時刻', '銘柄名(銘柄コード)', '注文']
        df = pd.DataFrame()

        # Date column
        if "発表日" in raw_df.columns:
            df["date"] = pd.to_datetime(raw_df["発表日"], format="%Y/%m/%d", errors="coerce")
        else:
            df["date"] = pd.to_datetime(target_date)

        # Time column
        if "発表時刻" in raw_df.columns:
            df["time"] = raw_df["発表時刻"].replace("-", None)
        else:
            df["time"] = None

        # Parse name and code from "銘柄名(銘柄コード)" column
        name_code_col = "銘柄名(銘柄コード)"
        if name_code_col in raw_df.columns:
            # Format: "トヨタ自動車(7203)"
            df["name"] = raw_df[name_code_col].str.extract(r"^(.+?)\(")[0]
            df["code"] = raw_df[name_code_col].str.extract(r"\((\w+)\)")[0]
        else:
            df["name"] = None
            df["code"] = None

        # Matsui doesn't provide earnings type in this view
        df["type"] = None

        return df
