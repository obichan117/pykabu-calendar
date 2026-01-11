"""
Tests for individual scrapers.

All tests use live data - no mocks.
"""

import pytest
import pandas as pd

from pykabu_calendar.scrapers import fetch_matsui, fetch_tradersweb, fetch_sbi
from pykabu_calendar.scrapers.config import (
    HEADERS,
    USER_AGENT,
    build_matsui_url,
    build_tradersweb_url,
    build_sbi_url,
)


TEST_DATE = "2026-02-10"


class TestConfig:
    """Tests for scraper configuration."""

    def test_user_agent_is_modern(self):
        """User-Agent should be modern Chrome."""
        assert "Chrome/131" in USER_AGENT
        assert "Windows NT 10.0" in USER_AGENT

    def test_headers_include_user_agent(self):
        """Headers should include User-Agent."""
        assert "User-Agent" in HEADERS
        assert HEADERS["User-Agent"] == USER_AGENT

    def test_build_matsui_url(self):
        """Should build correct Matsui URL."""
        url = build_matsui_url("2026-02-10")
        assert "finance.matsui.co.jp" in url
        assert "2026/2/10" in url

    def test_build_tradersweb_url(self):
        """Should build correct Tradersweb URL."""
        url = build_tradersweb_url("2026-02-10")
        assert "traders.co.jp" in url
        assert "2026/02/10" in url

    def test_build_sbi_url(self):
        """Should build correct SBI URL."""
        url = build_sbi_url("2026-02-10")
        assert "sbisec.co.jp" in url
        assert "202602" in url


class TestMatsui:
    """Tests for Matsui scraper."""

    def test_returns_dataframe(self):
        """Should return a DataFrame."""
        df = fetch_matsui(TEST_DATE)
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        """Should have code, name, datetime columns."""
        df = fetch_matsui(TEST_DATE)
        assert "code" in df.columns
        assert "name" in df.columns
        assert "datetime" in df.columns

    def test_code_is_string(self):
        """Code should be string type."""
        df = fetch_matsui(TEST_DATE)
        if not df.empty:
            assert df["code"].dtype == object


class TestTradersweb:
    """Tests for Tradersweb scraper."""

    def test_returns_dataframe(self):
        """Should return a DataFrame."""
        df = fetch_tradersweb(TEST_DATE)
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        """Should have code, name, datetime columns."""
        df = fetch_tradersweb(TEST_DATE)
        assert "code" in df.columns
        assert "name" in df.columns
        assert "datetime" in df.columns


@pytest.mark.slow
class TestSbi:
    """Tests for SBI scraper (requires Playwright)."""

    def test_returns_dataframe(self):
        """Should return a DataFrame."""
        df = fetch_sbi(TEST_DATE)
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        """Should have code, name, datetime columns."""
        df = fetch_sbi(TEST_DATE)
        assert "code" in df.columns
        assert "name" in df.columns
        assert "datetime" in df.columns
