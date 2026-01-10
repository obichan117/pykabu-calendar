"""
Tests for calendar aggregator.

All tests use live data - no mocks.
"""

import pytest
import pandas as pd

from pykabu_calendar import get_calendar, EarningsCalendar


TEST_DATE = "2026-01-20"
TEST_DATE_MANY = "2026-02-10"


class TestGetCalendar:
    """Tests for get_calendar function."""

    def test_returns_dataframe(self):
        """Should return a DataFrame."""
        df = get_calendar(TEST_DATE, infer_from_history=False)
        assert isinstance(df, pd.DataFrame)

    def test_has_datetime_column(self):
        """Should have datetime column."""
        df = get_calendar(TEST_DATE, infer_from_history=False)
        assert "datetime" in df.columns

    def test_has_time_source_column(self):
        """Should have time_source column."""
        df = get_calendar(TEST_DATE, infer_from_history=False)
        assert "time_source" in df.columns

    def test_infer_from_history_adds_columns(self):
        """Should add inference columns when enabled."""
        df = get_calendar(TEST_DATE, infer_from_history=True)
        assert "time_inferred" in df.columns
        assert "inference_confidence" in df.columns

    def test_specific_sources(self):
        """Should only use specified sources."""
        df = get_calendar(TEST_DATE, sources=["matsui"], infer_from_history=False)
        # Should only have matsui time column (plus standard columns)
        time_cols = [c for c in df.columns if c.startswith("time_") and c != "time_source"]
        assert "time_matsui" in time_cols
        assert "time_sbi" not in time_cols


class TestEarningsCalendar:
    """Tests for EarningsCalendar class."""

    def test_init_with_sources(self):
        """Should initialize with specified sources."""
        cal = EarningsCalendar(sources=["matsui", "tradersweb"])
        assert len(cal._scrapers) == 2

    def test_init_with_invalid_source(self):
        """Should skip invalid sources with warning."""
        cal = EarningsCalendar(sources=["matsui", "invalid_source"])
        assert len(cal._scrapers) == 1
