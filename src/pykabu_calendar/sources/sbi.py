"""
SBI Securities earnings calendar scraper.

SBI is the PRIMARY calendar source but requires browser automation
because it uses JavaScript templating to render data.

Requires: pip install pykabu-calendar[browser]
"""

import logging
from io import StringIO
from typing import Optional

import pandas as pd

from .base import BaseCalendarScraper, SourceUnavailableError

logger = logging.getLogger(__name__)


class SbiCalendarScraper(BaseCalendarScraper):
    """
    Scraper for SBI Securities earnings calendar.

    This is the PRIMARY source but requires Playwright for JavaScript rendering.
    Falls back gracefully if Playwright is not installed.
    """

    TABLE_CLASS = "md-table06"
    VIEW_BTN_TEXT = "100件"
    NEXT_BTN_TEXT = "次へ→"

    @property
    def name(self) -> str:
        return "sbi"

    def _get_url(self, target_date: str) -> str:
        """Build SBI calendar URL for target date."""
        year, month, day = target_date.split("-")
        return (
            f"https://www.sbisec.co.jp/ETGate/?"
            f"_ControlID=WPLETmgR001Control&"
            f"_PageID=WPLETmgR001Mdtl20&"
            f"_DataStoreID=DSWPLETmgR001Control&"
            f"_ActionID=DefaultAID&"
            f"burl=iris_economicCalendar&"
            f"cat1=market&cat2=economicCalender&"
            f"dir=tl1-cal%7Ctl2-schedule%7Ctl3-stock%7Ctl4-calsel%7C"
            f"tl9-{year}{month}%7Ctl10-{year}{month}{day}&"
            f"file=index.html&getFlg=on"
        )

    def _try_browser(self, target_date: str) -> Optional[pd.DataFrame]:
        """Scrape SBI calendar using Playwright."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.logger.warning(
                "Playwright not installed. Install with: pip install pykabu-calendar[browser]"
            )
            return None

        url = self._get_url(target_date)
        self.logger.debug(f"Fetching {url} with Playwright")

        all_dfs = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Navigate to page
                page.goto(url, timeout=self.timeout * 1000)

                # Wait for table to load
                page.wait_for_selector(f"table.{self.TABLE_CLASS}", timeout=10000)

                # Click 100件 button to show all entries
                try:
                    page.click(f"text={self.VIEW_BTN_TEXT}", timeout=5000)
                    page.wait_for_timeout(1000)  # Wait for reload
                except Exception:
                    pass  # Button might not exist if < 100 entries

                # Paginate through all pages
                while True:
                    # Get table HTML
                    table_element = page.query_selector(f"table.{self.TABLE_CLASS}")
                    if not table_element:
                        break

                    table_html = table_element.inner_html()
                    df = pd.read_html(StringIO(f"<table>{table_html}</table>"))[0]
                    all_dfs.append(df)

                    # Try to click next page
                    try:
                        next_btn = page.query_selector(f"text={self.NEXT_BTN_TEXT}")
                        if next_btn:
                            next_btn.click()
                            page.wait_for_timeout(1000)
                        else:
                            break
                    except Exception:
                        break

                browser.close()

        except Exception as e:
            self.logger.error(f"Playwright error: {e}")
            return None

        if not all_dfs:
            return pd.DataFrame(columns=self.OUTPUT_COLUMNS)

        raw_df = pd.concat(all_dfs, ignore_index=True)
        return self._parse_dataframe(raw_df, target_date)

    def _parse_dataframe(self, raw_df: pd.DataFrame, target_date: str) -> pd.DataFrame:
        """Parse raw SBI DataFrame into standard format."""
        # Expected columns from SBI:
        # ['発表日', '発表時刻', '銘柄名 銘柄コード', '種別',
        #  '今期経常', '会社予想', 'コンセンサス', '取引', 'ポートフォリオ']

        df = pd.DataFrame()

        # Date column
        # Some entries show approximate dates like "2026/02 上旬" (early Feb)
        # which can't be parsed as datetime - use target_date as fallback
        if "発表日" in raw_df.columns:
            df["date"] = pd.to_datetime(raw_df["発表日"], format="%Y/%m/%d", errors="coerce")
            # Fill NaN dates with target_date
            df["date"] = df["date"].fillna(pd.to_datetime(target_date))
        else:
            df["date"] = pd.to_datetime(target_date)

        # Time column - format: "15:30 (予定)" -> "15:30"
        time_col = None
        for col in raw_df.columns:
            if "時刻" in col:
                time_col = col
                break

        if time_col and time_col in raw_df.columns:
            df["time"] = raw_df[time_col].astype(str).str.extract(r"(\d{1,2}:\d{2})")[0]
        else:
            df["time"] = None

        # Name and code
        name_col = None
        for col in raw_df.columns:
            if "銘柄" in col:
                name_col = col
                break

        if name_col and name_col in raw_df.columns:
            # Format: "トヨタ自動車 (7203)" or "オリオンビール (409A)"
            df["name"] = raw_df[name_col].str.extract(r"^(.+?)\s*\(")[0]
            # Handle alphanumeric codes like "409A", "167A", etc.
            df["code"] = raw_df[name_col].str.extract(r"\((\w+)\)")[0]
        else:
            df["name"] = None
            df["code"] = None

        # Type column
        if "種別" in raw_df.columns:
            df["type"] = raw_df["種別"].str.replace(r"\n", "", regex=True)
        else:
            df["type"] = None

        return df
