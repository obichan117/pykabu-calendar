"""
Tradersweb earnings calendar scraper.

Tradersweb provides calendar data at traders.co.jp.
Works with plain requests - no browser automation needed.
"""

import logging
from io import StringIO
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup

from .base import BaseCalendarScraper, SourceUnavailableError

logger = logging.getLogger(__name__)


class TraderswebCalendarScraper(BaseCalendarScraper):
    """Scraper for Tradersweb earnings calendar."""

    BASE_URL = "https://www.traders.co.jp/market_jp/earnings_calendar"

    @property
    def name(self) -> str:
        return "tradersweb"

    def _try_scrape(self, target_date: str) -> Optional[pd.DataFrame]:
        """Scrape Tradersweb calendar via requests."""
        # Tradersweb uses date format YYYY/MM/DD in the URL
        year, month, day = target_date.split("-")
        date_param = f"{year}/{month}/{day}"

        # URL format: /market_jp/earnings_calendar/all/all/1?term=2026/01/20
        url = f"{self.BASE_URL}/all/all/1?term={date_param}"
        self.logger.debug(f"Fetching {url}")

        try:
            response = self._request(url)
        except SourceUnavailableError as e:
            self.logger.error(f"Failed to fetch Tradersweb: {e}")
            return None

        soup = BeautifulSoup(response.text, "lxml")

        # Find the data table with class 'data_table'
        table = soup.find("table", class_="data_table")
        if not table:
            self.logger.warning("Table not found on Tradersweb page")
            # Try without specific date - get today's calendar
            return self._scrape_default_calendar()

        # Parse table
        try:
            df = pd.read_html(StringIO(str(table)))[0]
        except ValueError as e:
            self.logger.warning(f"Failed to parse table: {e}")
            return pd.DataFrame(columns=self.OUTPUT_COLUMNS)

        if df.empty:
            return pd.DataFrame(columns=self.OUTPUT_COLUMNS)

        return self._parse_dataframe(df, target_date)

    def _scrape_default_calendar(self) -> Optional[pd.DataFrame]:
        """Scrape the default calendar page (today's data)."""
        url = self.BASE_URL
        self.logger.debug(f"Fetching default calendar: {url}")

        try:
            response = self._request(url)
        except SourceUnavailableError as e:
            self.logger.error(f"Failed to fetch Tradersweb: {e}")
            return None

        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find("table", class_="data_table")

        if not table:
            return pd.DataFrame(columns=self.OUTPUT_COLUMNS)

        try:
            df = pd.read_html(StringIO(str(table)))[0]
        except ValueError:
            return pd.DataFrame(columns=self.OUTPUT_COLUMNS)

        # Use current year for parsing
        from datetime import datetime

        return self._parse_dataframe(df, datetime.now().strftime("%Y-%m-%d"))

    def _parse_dataframe(self, raw_df: pd.DataFrame, target_date: str) -> pd.DataFrame:
        """Parse raw Tradersweb DataFrame into standard format."""
        # Expected columns:
        # ['発表日', '時刻', '銘柄名\n(コード/市場)', '決算種別', '業種', '時価総額(億円)', '関連情報']

        df = pd.DataFrame()
        year = target_date.split("-")[0]

        # Date column - format: "01/20"
        if "発表日" in raw_df.columns:
            # Convert MM/DD to full date
            df["date"] = pd.to_datetime(
                year + "/" + raw_df["発表日"].astype(str), format="%Y/%m/%d", errors="coerce"
            )
        else:
            df["date"] = pd.to_datetime(target_date)

        # Time column
        if "時刻" in raw_df.columns:
            df["time"] = raw_df["時刻"].replace("-", None)
        else:
            df["time"] = None

        # Parse name and code
        # Format: "銘柄名\n(コード/市場)" contains "トヨタ自動車\n\n\n(7203/東P)"
        name_col = None
        for col in raw_df.columns:
            if "銘柄名" in col:
                name_col = col
                break

        if name_col:
            # Extract name (before the code part)
            # Format: "トヨタ自動車  (7203/東P)"
            df["name"] = raw_df[name_col].str.extract(r"^([^(]+)")[0].str.strip()
            # Extract code (alphanumeric, e.g., "7203" or "189A")
            df["code"] = raw_df[name_col].str.extract(r"\((\w+)/")[0]
        else:
            df["name"] = None
            df["code"] = None

        # Type column
        if "決算種別" in raw_df.columns:
            df["type"] = raw_df["決算種別"]
        else:
            df["type"] = None

        # Filter out header rows (where code is not alphanumeric)
        df = df[df["code"].str.match(r"^\w+$", na=False)]

        return df
