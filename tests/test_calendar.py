"""
Tests for calendar aggregator.

Integration tests (live network) are marked @pytest.mark.slow.
"""

import pandas as pd
import pytest

from pykabu_calendar import get_calendar, export_to_csv

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from conftest import get_test_date


@pytest.mark.slow
class TestGetCalendar:
    """Tests for get_calendar function (live network)."""

    def test_returns_dataframe(self):
        """Should return a DataFrame."""
        df = get_calendar(get_test_date(), infer_from_history=False, include_ir=False)
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        """Should have required columns."""
        df = get_calendar(get_test_date(), infer_from_history=False, include_ir=False)
        assert "code" in df.columns
        assert "name" in df.columns
        assert "datetime" in df.columns
        assert "candidate_datetimes" in df.columns

    def test_has_source_datetime_columns(self):
        """Should have source-specific datetime columns."""
        df = get_calendar(get_test_date(), infer_from_history=False, include_ir=False)
        assert "matsui_datetime" in df.columns
        assert "tradersweb_datetime" in df.columns

    def test_infer_from_history_adds_columns(self):
        """Should add inference columns when enabled."""
        df = get_calendar(get_test_date(), infer_from_history=True, include_ir=False)
        assert "inferred_datetime" in df.columns
        assert "past_datetimes" in df.columns

    def test_include_ir_adds_column(self):
        """Should add ir_datetime column when IR enabled."""
        df = get_calendar(
            get_test_date(),
            sources=["matsui"],
            infer_from_history=False,
            include_ir=True,
        )
        assert "ir_datetime" in df.columns

    def test_exclude_ir(self):
        """Should not have ir_datetime when IR disabled."""
        df = get_calendar(get_test_date(), infer_from_history=False, include_ir=False)
        assert "ir_datetime" not in df.columns

    def test_specific_sources(self):
        """Should only use specified sources."""
        df = get_calendar(
            get_test_date(), sources=["matsui"], infer_from_history=False, include_ir=False
        )
        assert "matsui_datetime" in df.columns
        # tradersweb should not be present when not requested
        assert "tradersweb_datetime" not in df.columns

    def test_candidate_datetimes_is_list(self):
        """candidate_datetimes should contain lists."""
        df = get_calendar(get_test_date(), infer_from_history=False, include_ir=False)
        if not df.empty:
            for val in df["candidate_datetimes"]:
                if val:
                    assert isinstance(val, list)
                    break

    def test_past_datetimes_is_list(self):
        """past_datetimes should contain lists when inference is enabled."""
        df = get_calendar(get_test_date(), infer_from_history=True, include_ir=False)
        if not df.empty:
            non_null = df["past_datetimes"].dropna()
            if not non_null.empty:
                val = non_null.iloc[0]
                assert isinstance(val, list)

    def test_returns_non_empty(self):
        """Should return non-empty DataFrame for valid date."""
        df = get_calendar(get_test_date(), infer_from_history=False, include_ir=False)
        assert len(df) > 0, f"Expected earnings data for {get_test_date()}"


@pytest.mark.slow
class TestExportToCsv:
    """Tests for export_to_csv function (live network)."""

    def test_export_creates_file(self, tmp_path):
        """Should create a CSV file."""
        df = get_calendar(get_test_date(), infer_from_history=False, include_ir=False)
        path = tmp_path / "test.csv"
        export_to_csv(df, str(path))
        assert path.exists()

    def test_export_is_readable(self, tmp_path):
        """Exported CSV should be readable."""
        df = get_calendar(get_test_date(), infer_from_history=False, include_ir=False)
        path = tmp_path / "test.csv"
        export_to_csv(df, str(path))

        df_read = pd.read_csv(path)
        assert len(df_read) == len(df)
