"""
Tests for calendar source scrapers.

All tests use live data - no mocks.
"""

import pytest
import pandas as pd

from pykabu_calendar.sources import (
    SbiCalendarScraper,
    MatsuiCalendarScraper,
    TraderswebCalendarScraper,
)


# Test fixtures - dates with known earnings data
TEST_DATE_WITH_DATA = "2026-02-10"  # Q3 earnings season
TEST_DATE_FEW_ENTRIES = "2026-01-20"


class TestMatsuiScraper:
    """Tests for Matsui calendar scraper."""

    @pytest.fixture
    def scraper(self):
        return MatsuiCalendarScraper(timeout=60)

    def test_get_calendar_returns_dataframe(self, scraper):
        """Should return a DataFrame."""
        df = scraper.get_calendar(TEST_DATE_WITH_DATA)
        assert isinstance(df, pd.DataFrame)

    def test_get_calendar_has_required_columns(self, scraper):
        """Should have required columns."""
        df = scraper.get_calendar(TEST_DATE_WITH_DATA)
        required = ["code", "date", "time", "name", "type"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_get_calendar_code_is_string(self, scraper):
        """Code column should be string type."""
        df = scraper.get_calendar(TEST_DATE_WITH_DATA)
        if not df.empty:
            assert df["code"].dtype == object  # string

    def test_get_calendar_returns_data(self, scraper):
        """Should return data for a date with known earnings."""
        df = scraper.get_calendar(TEST_DATE_WITH_DATA)
        assert len(df) > 0, "Expected data but got empty DataFrame"


class TestTraderswebScraper:
    """Tests for Tradersweb calendar scraper."""

    @pytest.fixture
    def scraper(self):
        return TraderswebCalendarScraper(timeout=60)

    def test_get_calendar_returns_dataframe(self, scraper):
        """Should return a DataFrame."""
        df = scraper.get_calendar(TEST_DATE_WITH_DATA)
        assert isinstance(df, pd.DataFrame)

    def test_get_calendar_has_required_columns(self, scraper):
        """Should have required columns."""
        df = scraper.get_calendar(TEST_DATE_WITH_DATA)
        required = ["code", "date", "time", "name", "type"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_get_calendar_code_format(self, scraper):
        """Code should be alphanumeric (e.g., '7203' or '189A')."""
        df = scraper.get_calendar(TEST_DATE_WITH_DATA)
        if not df.empty:
            for code in df["code"].dropna():
                assert code.isalnum(), f"Invalid code format: {code}"


@pytest.mark.slow
class TestSbiScraper:
    """
    Tests for SBI calendar scraper.

    Marked as slow because SBI requires Playwright/browser automation.
    """

    @pytest.fixture
    def scraper(self):
        return SbiCalendarScraper(timeout=90)

    def test_get_calendar_returns_dataframe(self, scraper):
        """Should return a DataFrame."""
        df = scraper.get_calendar(TEST_DATE_FEW_ENTRIES)
        assert isinstance(df, pd.DataFrame)

    def test_get_calendar_has_required_columns(self, scraper):
        """Should have required columns."""
        df = scraper.get_calendar(TEST_DATE_FEW_ENTRIES)
        required = ["code", "date", "time", "name", "type"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_get_calendar_has_time_data(self, scraper):
        """SBI should provide time data."""
        df = scraper.get_calendar(TEST_DATE_FEW_ENTRIES)
        if not df.empty:
            # At least some entries should have time
            time_notna = df["time"].notna().sum()
            assert time_notna > 0, "Expected some time data from SBI"

    def test_get_calendar_pagination(self, scraper):
        """Should handle pagination for dates with many entries."""
        df = scraper.get_calendar(TEST_DATE_WITH_DATA)
        # Expect more than 100 entries (requires pagination)
        assert len(df) > 100, f"Expected >100 entries, got {len(df)}"
