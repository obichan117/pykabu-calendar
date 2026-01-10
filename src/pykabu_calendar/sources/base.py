"""
Base calendar scraper interface.

Implements a hybrid scraping strategy:
1. Try backend API (if discoverable)
2. Try requests + BeautifulSoup (lightweight)
3. Fall back to Playwright/Selenium (if JS required)
"""

import logging
from abc import ABC, abstractmethod
from io import StringIO
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

# User agent to avoid 403 Forbidden
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT = 30


class CalendarScraperError(Exception):
    """Base exception for scraper errors."""

    pass


class SourceUnavailableError(CalendarScraperError):
    """Raised when a calendar source is unavailable."""

    pass


class MaxDateExceededError(CalendarScraperError):
    """Raised when requesting calendar too far into the future."""

    pass


class BaseCalendarScraper(ABC):
    """
    Abstract base class for calendar scrapers.

    Subclasses must implement:
    - name: str property identifying the source
    - get_calendar(target_date) -> DataFrame

    Subclasses should implement one of:
    - _try_api(): attempt to fetch via backend API
    - _try_scrape(): attempt to scrape via requests/BeautifulSoup
    - _try_browser(): attempt to scrape via browser automation

    The default get_calendar() implementation tries each method in order.
    """

    # Standard output columns
    OUTPUT_COLUMNS = ["code", "date", "time", "name", "type"]

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._session: Optional[requests.Session] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Source name (e.g., 'sbi', 'matsui')."""
        pass

    @property
    def session(self) -> requests.Session:
        """Lazy-initialized requests session."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({"User-Agent": USER_AGENT})
        return self._session

    def get_calendar(self, target_date: str) -> pd.DataFrame:
        """
        Get earnings calendar for target date.

        Args:
            target_date: Date string in YYYY-MM-DD format

        Returns:
            DataFrame with columns: code, date, time, name, type
        """
        self.logger.info(f"[{self.name}] Fetching calendar for {target_date}")

        # Try API first (fastest)
        df = self._try_api(target_date)
        if df is not None and not df.empty:
            self.logger.info(f"[{self.name}] Got {len(df)} entries via API")
            return self._normalize_output(df)

        # Try lightweight scraping
        df = self._try_scrape(target_date)
        if df is not None and not df.empty:
            self.logger.info(f"[{self.name}] Got {len(df)} entries via scrape")
            return self._normalize_output(df)

        # Try browser automation (slowest)
        df = self._try_browser(target_date)
        if df is not None and not df.empty:
            self.logger.info(f"[{self.name}] Got {len(df)} entries via browser")
            return self._normalize_output(df)

        self.logger.warning(f"[{self.name}] No data found for {target_date}")
        return pd.DataFrame(columns=self.OUTPUT_COLUMNS)

    def _try_api(self, target_date: str) -> Optional[pd.DataFrame]:
        """
        Attempt to fetch via backend API.

        Override in subclass if API endpoint is known.
        Returns None if not implemented or failed.
        """
        return None

    def _try_scrape(self, target_date: str) -> Optional[pd.DataFrame]:
        """
        Attempt to scrape via requests + BeautifulSoup.

        Override in subclass. Returns None if not implemented or failed.
        """
        return None

    def _try_browser(self, target_date: str) -> Optional[pd.DataFrame]:
        """
        Attempt to scrape via browser automation.

        Override in subclass if JS rendering is required.
        Returns None if not implemented or failed.
        """
        return None

    def _normalize_output(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure output has standard columns."""
        # Ensure required columns exist
        for col in self.OUTPUT_COLUMNS:
            if col not in df.columns:
                df[col] = None

        # Ensure code is string
        if "code" in df.columns:
            df["code"] = df["code"].astype(str)

        return df[self.OUTPUT_COLUMNS]

    # Helper methods for subclasses

    def _request(self, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with timeout and error handling."""
        try:
            response = self.session.get(url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response
        except requests.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise SourceUnavailableError(f"Failed to fetch {url}: {e}") from e

    def _get_soup(self, url: str) -> BeautifulSoup:
        """Get BeautifulSoup object from URL."""
        response = self._request(url)
        return BeautifulSoup(response.text, features="lxml")

    def _read_html(self, url: str, **kwargs) -> list[pd.DataFrame]:
        """Read HTML tables from URL into DataFrames."""
        response = self._request(url)
        return pd.read_html(StringIO(response.text), **kwargs)

    def _soup_to_dfs(
        self, soup: BeautifulSoup, match: Optional[str] = None, **kwargs
    ) -> list[pd.DataFrame]:
        """Convert BeautifulSoup object to list of DataFrames."""
        return pd.read_html(StringIO(str(soup)), match=match, **kwargs)
