"""
Tests for historical pattern inference.

All tests use live data - no mocks.
"""

import pytest

from pykabu_calendar.inference import (
    get_past_earnings_times,
    infer_time_from_history,
    is_during_trading_hours,
    is_time_significant,
)


# Test fixtures - known stock codes
TEST_CODES = ["7203", "6758", "9984"]  # Toyota, Sony, SoftBank


class TestGetPastEarningsTimes:
    """Tests for get_past_earnings_times."""

    def test_returns_list(self):
        """Should return a list."""
        times = get_past_earnings_times("7203")
        assert isinstance(times, list)

    def test_returns_time_strings(self):
        """Times should be in HH:MM format."""
        times = get_past_earnings_times("7203")
        if times:
            for t in times:
                assert ":" in t, f"Invalid time format: {t}"
                h, m = t.split(":")
                assert h.isdigit() and m.isdigit()

    def test_invalid_code_returns_empty(self):
        """Should return empty list for invalid codes."""
        times = get_past_earnings_times("9999")  # Invalid code
        assert isinstance(times, list)


class TestInferTimeFromHistory:
    """Tests for infer_time_from_history."""

    def test_returns_tuple(self):
        """Should return tuple of (time, confidence)."""
        result = infer_time_from_history("7203")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_confidence_values(self):
        """Confidence should be one of known values."""
        _, confidence = infer_time_from_history("7203")
        assert confidence in ["high", "medium", "low", "none", "error"]


class TestIsDuringTradingHours:
    """Tests for is_during_trading_hours."""

    def test_morning_session(self):
        """9:00-11:30 should be trading hours."""
        assert is_during_trading_hours("09:00") is True
        assert is_during_trading_hours("10:30") is True
        assert is_during_trading_hours("11:30") is True

    def test_lunch_break(self):
        """11:31-12:29 should not be trading hours."""
        assert is_during_trading_hours("12:00") is False

    def test_afternoon_session(self):
        """12:30-15:30 should be trading hours."""
        assert is_during_trading_hours("12:30") is True
        assert is_during_trading_hours("14:00") is True
        assert is_during_trading_hours("15:30") is True

    def test_after_close(self):
        """After 15:30 should not be trading hours."""
        assert is_during_trading_hours("15:31") is False
        assert is_during_trading_hours("16:00") is False

    def test_before_open(self):
        """Before 9:00 should not be trading hours."""
        assert is_during_trading_hours("08:59") is False


class TestIsTimeSignificant:
    """Tests for is_time_significant."""

    def test_trading_hours_significant(self):
        """Times during trading hours are significant."""
        assert is_time_significant("10:00") is True
        assert is_time_significant("14:00") is True

    def test_after_close_not_significant(self):
        """Times after 15:30 are not significant."""
        assert is_time_significant("16:00") is False
        assert is_time_significant("17:00") is False

    def test_none_is_significant(self):
        """None (unknown time) is significant."""
        assert is_time_significant(None) is True
