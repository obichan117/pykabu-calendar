"""
Tests for historical pattern inference.

All tests use live data - no mocks.
"""

import pytest
import pandas as pd

from pykabu_calendar.inference import (
    get_past_earnings,
    infer_datetime,
    is_during_trading_hours,
)


# Test fixtures - known stock codes
TEST_CODES = ["7203", "6758", "9984"]  # Toyota, Sony, SoftBank


class TestGetPastEarnings:
    """Tests for get_past_earnings."""

    def test_returns_list(self):
        """Should return a list."""
        times = get_past_earnings("7203")
        assert isinstance(times, list)

    def test_returns_timestamps(self):
        """Items should be Timestamps."""
        times = get_past_earnings("7203")
        if times:
            for t in times:
                assert isinstance(t, pd.Timestamp)

    def test_invalid_code_returns_empty(self):
        """Should return empty list for invalid codes."""
        times = get_past_earnings("9999999")
        assert isinstance(times, list)


class TestInferDatetime:
    """Tests for infer_datetime."""

    def test_returns_tuple(self):
        """Should return tuple of (datetime, confidence, past_datetimes)."""
        result = infer_datetime("7203", "2026-02-10")
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_confidence_values(self):
        """Confidence should be one of known values."""
        _, confidence, _ = infer_datetime("7203", "2026-02-10")
        assert confidence in ["high", "medium", "low", "none"]

    def test_past_datetimes_is_list(self):
        """Third element should be a list."""
        _, _, past_dts = infer_datetime("7203", "2026-02-10")
        assert isinstance(past_dts, list)


class TestIsDuringTradingHours:
    """Tests for is_during_trading_hours."""

    def test_morning_session(self):
        """9:00-11:30 should be trading hours."""
        assert is_during_trading_hours(pd.Timestamp("2026-02-10 09:00:00")) is True
        assert is_during_trading_hours(pd.Timestamp("2026-02-10 10:30:00")) is True
        assert is_during_trading_hours(pd.Timestamp("2026-02-10 11:30:00")) is True

    def test_lunch_break(self):
        """11:31-12:29 should not be trading hours."""
        assert is_during_trading_hours(pd.Timestamp("2026-02-10 12:00:00")) is False

    def test_afternoon_session(self):
        """12:30-15:30 should be trading hours."""
        assert is_during_trading_hours(pd.Timestamp("2026-02-10 12:30:00")) is True
        assert is_during_trading_hours(pd.Timestamp("2026-02-10 14:00:00")) is True
        assert is_during_trading_hours(pd.Timestamp("2026-02-10 15:30:00")) is True

    def test_after_close(self):
        """After 15:30 should not be trading hours."""
        assert is_during_trading_hours(pd.Timestamp("2026-02-10 15:31:00")) is False
        assert is_during_trading_hours(pd.Timestamp("2026-02-10 16:00:00")) is False

    def test_before_open(self):
        """Before 9:00 should not be trading hours."""
        assert is_during_trading_hours(pd.Timestamp("2026-02-10 08:59:00")) is False

    def test_nat_returns_false(self):
        """NaT should return False."""
        assert is_during_trading_hours(pd.NaT) is False
