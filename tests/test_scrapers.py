"""
Tests for individual scrapers.

All tests use live data - no mocks.
Uses dynamic dates to ensure tests work regardless of when they're run.
"""

import pandas as pd

from pykabu_calendar.earnings.sources import get_matsui, get_tradersweb, get_sbi
from pykabu_calendar.config import get_settings
from pykabu_calendar.earnings.sources.matsui import build_url as build_matsui_url
from pykabu_calendar.earnings.sources.tradersweb import build_url as build_tradersweb_url
from pykabu_calendar.earnings.sources.sbi import build_url as build_sbi_url

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from conftest import get_test_date


class TestConfig:
    """Tests for scraper configuration."""

    def test_user_agent_is_modern(self):
        """User-Agent should be modern Chrome."""
        settings = get_settings()
        assert "Chrome/131" in settings.user_agent
        assert "Windows NT 10.0" in settings.user_agent

    def test_headers_include_user_agent(self):
        """Headers should include User-Agent."""
        settings = get_settings()
        assert "User-Agent" in settings.headers
        assert settings.headers["User-Agent"] == settings.user_agent

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
        df = get_matsui(get_test_date())
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        """Should have code, name, datetime columns."""
        df = get_matsui(get_test_date())
        assert "code" in df.columns
        assert "name" in df.columns
        assert "datetime" in df.columns

    def test_code_is_string(self):
        """Code should be string type."""
        df = get_matsui(get_test_date())
        if not df.empty:
            assert df["code"].dtype == object

    def test_returns_non_empty(self):
        """Should return non-empty DataFrame for valid date."""
        df = get_matsui(get_test_date())
        assert len(df) > 0, f"Expected earnings data for {get_test_date()}"


class TestTradersweb:
    """Tests for Tradersweb scraper."""

    def test_returns_dataframe(self):
        """Should return a DataFrame."""
        df = get_tradersweb(get_test_date())
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        """Should have code, name, datetime columns."""
        df = get_tradersweb(get_test_date())
        assert "code" in df.columns
        assert "name" in df.columns
        assert "datetime" in df.columns


class TestSbi:
    """Tests for SBI scraper."""

    def test_returns_dataframe(self):
        """Should return a DataFrame."""
        df = get_sbi(get_test_date())
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        """Should have code, name, datetime columns."""
        df = get_sbi(get_test_date())
        assert "code" in df.columns
        assert "name" in df.columns
        assert "datetime" in df.columns
