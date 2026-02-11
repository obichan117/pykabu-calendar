"""Tests for EarningsSource ABC and validation."""

import pandas as pd
import pytest

from pykabu_calendar.earnings.base import EarningsSource


class DummySource(EarningsSource):
    """Concrete subclass for testing."""

    @property
    def name(self) -> str:
        return "dummy"

    def _fetch(self, date: str) -> pd.DataFrame:
        return self._data

    def set_data(self, df: pd.DataFrame):
        self._data = df


class TestFetchValidation:
    """Tests for EarningsSource.fetch() validation logic."""

    @pytest.fixture
    def source(self):
        s = DummySource()
        s.set_data(pd.DataFrame())
        return s

    def test_empty_dataframe_passthrough(self, source):
        """Empty DataFrame should pass through unchanged."""
        source.set_data(pd.DataFrame())
        result = source.fetch("2026-02-10")
        assert result.empty

    def test_valid_data(self, source):
        """Valid data should pass validation."""
        source.set_data(pd.DataFrame({
            "code": ["7203", "6758"],
            "name": ["Toyota", "Sony"],
            "datetime": ["2026-02-10 15:00", "2026-02-10 16:00"],
        }))
        result = source.fetch("2026-02-10")
        assert len(result) == 2
        assert result["code"].dtype == object
        assert pd.api.types.is_datetime64_any_dtype(result["datetime"])

    def test_missing_code_column(self, source):
        """Missing 'code' column should return empty DataFrame."""
        source.set_data(pd.DataFrame({
            "name": ["Toyota"],
            "datetime": ["2026-02-10 15:00"],
        }))
        result = source.fetch("2026-02-10")
        assert result.empty
        assert "code" in result.columns

    def test_missing_datetime_column(self, source):
        """Missing 'datetime' column should return empty DataFrame."""
        source.set_data(pd.DataFrame({
            "code": ["7203"],
            "name": ["Toyota"],
        }))
        result = source.fetch("2026-02-10")
        assert result.empty

    def test_invalid_code_dropped(self, source):
        """Rows with invalid codes should be dropped."""
        source.set_data(pd.DataFrame({
            "code": ["7203", "TOOLONG", "AB"],
            "name": ["Toyota", "Bad", "Also Bad"],
            "datetime": ["2026-02-10 15:00", "2026-02-10 15:00", "2026-02-10 15:00"],
        }))
        result = source.fetch("2026-02-10")
        assert len(result) == 1
        assert result.iloc[0]["code"] == "7203"

    def test_code_coerced_to_string(self, source):
        """Numeric codes should be coerced to strings."""
        source.set_data(pd.DataFrame({
            "code": [7203, 6758],
            "name": ["Toyota", "Sony"],
            "datetime": ["2026-02-10 15:00", "2026-02-10 16:00"],
        }))
        result = source.fetch("2026-02-10")
        assert len(result) == 2
        assert result["code"].dtype == object
        assert result.iloc[0]["code"] == "7203"

    def test_datetime_coercion(self, source):
        """Datetime strings should be coerced to Timestamps."""
        source.set_data(pd.DataFrame({
            "code": ["7203"],
            "name": ["Toyota"],
            "datetime": ["2026-02-10 15:00:00"],
        }))
        result = source.fetch("2026-02-10")
        assert pd.api.types.is_datetime64_any_dtype(result["datetime"])

    def test_nat_datetime_kept(self, source):
        """NaT datetimes should be kept (time unknown is valid)."""
        source.set_data(pd.DataFrame({
            "code": ["7203"],
            "name": ["Toyota"],
            "datetime": [pd.NaT],
        }))
        result = source.fetch("2026-02-10")
        assert len(result) == 1


class TestCheck:
    """Tests for EarningsSource.check() health check."""

    def test_check_returns_dict(self):
        """check() should return dict with expected keys."""
        source = DummySource()
        source._config = {"health_check": {"test_date": "2026-02-10", "min_rows": 0}}
        source.set_data(pd.DataFrame({
            "code": ["7203"],
            "name": ["Toyota"],
            "datetime": ["2026-02-10 15:00"],
        }))
        result = source.check()
        assert result["name"] == "dummy"
        assert result["ok"] is True
        assert result["rows"] == 1
        assert result["error"] is None

    def test_check_fails_below_min_rows(self):
        """check() should fail when rows < min_rows."""
        source = DummySource()
        source._config = {"health_check": {"test_date": "2026-02-10", "min_rows": 10}}
        source.set_data(pd.DataFrame({
            "code": ["7203"],
            "name": ["Toyota"],
            "datetime": ["2026-02-10 15:00"],
        }))
        result = source.check()
        assert result["ok"] is False
        assert "Expected >= 10" in result["error"]

    def test_check_handles_exception(self):
        """check() should catch exceptions."""
        source = DummySource()
        source._config = {}
        source._data = None  # Will cause _fetch to fail

        # Override _fetch to raise
        def bad_fetch(date):
            raise RuntimeError("Network error")
        source._fetch = bad_fetch

        result = source.check()
        assert result["ok"] is False
        assert "Network error" in result["error"]
