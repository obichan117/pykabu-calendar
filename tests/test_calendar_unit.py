"""
Unit tests for calendar aggregator internals.

These tests use mocks - no network required. Tests cover:
- _merge_sources: merging DataFrames from multiple sources
- _build_candidates: confidence scoring and candidate selection
- _empty_result: schema validation
- check_sources: health check aggregation
- get_calendar: top-level with mocked sources
"""

from unittest.mock import patch, MagicMock

import pandas as pd

from pykabu_calendar.earnings.calendar import (
    _merge_sources,
    _build_candidates,
    _empty_result,
    check_sources,
    get_calendar,
    OUTPUT_COLUMNS,
)


# --- Helpers ---

def _make_source_df(codes, names, datetimes):
    """Create a source DataFrame with standard columns."""
    return pd.DataFrame({
        "code": codes,
        "name": names,
        "datetime": [pd.Timestamp(dt) if dt else pd.NaT for dt in datetimes],
    })


# --- _empty_result ---

class TestEmptyResult:
    def test_returns_dataframe(self):
        result = _empty_result()
        assert isinstance(result, pd.DataFrame)

    def test_has_all_output_columns(self):
        result = _empty_result()
        assert list(result.columns) == OUTPUT_COLUMNS

    def test_is_empty(self):
        result = _empty_result()
        assert len(result) == 0


# --- _merge_sources ---

class TestMergeSources:
    def test_single_source(self):
        data = {
            "sbi": _make_source_df(["7203"], ["Toyota"], ["2026-02-10 15:00"]),
        }
        result = _merge_sources(data)
        assert "sbi_datetime" in result.columns
        assert len(result) == 1
        assert result["code"].iloc[0] == "7203"

    def test_two_sources_same_code(self):
        data = {
            "sbi": _make_source_df(["7203"], ["Toyota"], ["2026-02-10 15:00"]),
            "matsui": _make_source_df(["7203"], ["Toyota"], ["2026-02-10 15:30"]),
        }
        result = _merge_sources(data)
        assert "sbi_datetime" in result.columns
        assert "matsui_datetime" in result.columns
        assert len(result) == 1

    def test_two_sources_different_codes(self):
        data = {
            "sbi": _make_source_df(["7203"], ["Toyota"], ["2026-02-10 15:00"]),
            "matsui": _make_source_df(["6758"], ["Sony"], ["2026-02-10 16:00"]),
        }
        result = _merge_sources(data)
        assert len(result) == 2

    def test_three_sources_outer_join(self):
        data = {
            "sbi": _make_source_df(["7203", "6758"], ["Toyota", "Sony"], ["2026-02-10 15:00", "2026-02-10 16:00"]),
            "matsui": _make_source_df(["7203"], ["Toyota"], ["2026-02-10 15:00"]),
            "tradersweb": _make_source_df(["9984"], ["SoftBank"], ["2026-02-10 17:00"]),
        }
        result = _merge_sources(data)
        assert len(result) == 3
        assert set(result["code"]) == {"7203", "6758", "9984"}

    def test_name_preserved_from_first_source(self):
        """Name from first source should be kept when available."""
        df1 = pd.DataFrame({
            "code": ["7203"],
            "name": ["Toyota"],
            "datetime": [pd.Timestamp("2026-02-10 15:00")],
        })
        df2 = pd.DataFrame({
            "code": ["7203"],
            "name": ["トヨタ"],
            "datetime": [pd.Timestamp("2026-02-10 15:00")],
        })
        result = _merge_sources({"sbi": df1, "matsui": df2})
        assert result["name"].iloc[0] == "Toyota"


# --- _build_candidates ---

class TestBuildCandidates:
    def test_ir_datetime_is_highest_confidence(self):
        """IR datetime should get 'highest' confidence."""
        df = pd.DataFrame({
            "code": ["7203"],
            "ir_datetime": [pd.Timestamp("2026-02-10 15:00")],
            "sbi_datetime": [pd.Timestamp("2026-02-10 16:00")],
        })
        result = _build_candidates(df)
        assert result["confidence"].iloc[0] == "highest"
        assert result["datetime"].iloc[0] == pd.Timestamp("2026-02-10 15:00")

    def test_inferred_matches_scraper_is_high(self):
        """Inferred matching a scraper should get 'high' confidence."""
        df = pd.DataFrame({
            "code": ["7203"],
            "inferred_datetime": [pd.Timestamp("2026-02-10 15:00")],
            "sbi_datetime": [pd.Timestamp("2026-02-10 15:00")],
        })
        result = _build_candidates(df)
        assert result["confidence"].iloc[0] == "high"

    def test_two_scrapers_agree_is_high(self):
        """Two scrapers agreeing on time should get 'high' confidence."""
        df = pd.DataFrame({
            "code": ["7203"],
            "sbi_datetime": [pd.Timestamp("2026-02-10 15:00")],
            "matsui_datetime": [pd.Timestamp("2026-02-10 15:00")],
        })
        result = _build_candidates(df)
        assert result["confidence"].iloc[0] == "high"

    def test_two_scrapers_disagree_is_medium(self):
        """Two scrapers disagreeing should get 'medium' confidence."""
        df = pd.DataFrame({
            "code": ["7203"],
            "sbi_datetime": [pd.Timestamp("2026-02-10 15:00")],
            "matsui_datetime": [pd.Timestamp("2026-02-10 16:00")],
        })
        result = _build_candidates(df)
        assert result["confidence"].iloc[0] == "medium"

    def test_single_source_is_low(self):
        """Single source should get 'low' confidence."""
        df = pd.DataFrame({
            "code": ["7203"],
            "sbi_datetime": [pd.Timestamp("2026-02-10 15:00")],
        })
        result = _build_candidates(df)
        assert result["confidence"].iloc[0] == "low"

    def test_no_values_is_low(self):
        """No datetime values should get 'low' confidence and NaT."""
        df = pd.DataFrame({
            "code": ["7203"],
            "sbi_datetime": [pd.NaT],
            "matsui_datetime": [pd.NaT],
        })
        result = _build_candidates(df)
        assert result["confidence"].iloc[0] == "low"
        assert pd.isna(result["datetime"].iloc[0])

    def test_priority_order_without_agreement(self):
        """Without agreement, priority: inferred > sbi > matsui > tradersweb."""
        df = pd.DataFrame({
            "code": ["7203"],
            "inferred_datetime": [pd.Timestamp("2026-02-10 14:00")],
            "sbi_datetime": [pd.Timestamp("2026-02-10 15:00")],
            "matsui_datetime": [pd.Timestamp("2026-02-10 16:00")],
        })
        result = _build_candidates(df)
        # inferred doesn't match any scraper and scrapers disagree
        # So fallback to priority order — inferred first
        assert result["datetime"].iloc[0] == pd.Timestamp("2026-02-10 14:00")

    def test_candidate_datetimes_is_list(self):
        df = pd.DataFrame({
            "code": ["7203"],
            "sbi_datetime": [pd.Timestamp("2026-02-10 15:00")],
        })
        result = _build_candidates(df)
        assert isinstance(result["candidate_datetimes"].iloc[0], list)

    def test_ir_overrides_scrapers(self):
        """IR should be selected even when scrapers agree on different time."""
        df = pd.DataFrame({
            "code": ["7203"],
            "ir_datetime": [pd.Timestamp("2026-02-10 14:00")],
            "sbi_datetime": [pd.Timestamp("2026-02-10 15:00")],
            "matsui_datetime": [pd.Timestamp("2026-02-10 15:00")],
        })
        result = _build_candidates(df)
        assert result["datetime"].iloc[0] == pd.Timestamp("2026-02-10 14:00")
        assert result["confidence"].iloc[0] == "highest"

    def test_multiple_rows(self):
        """Should handle multiple rows independently."""
        df = pd.DataFrame({
            "code": ["7203", "6758"],
            "ir_datetime": [pd.Timestamp("2026-02-10 14:00"), pd.NaT],
            "sbi_datetime": [pd.NaT, pd.Timestamp("2026-02-10 15:00")],
        })
        result = _build_candidates(df)
        assert result["confidence"].iloc[0] == "highest"
        assert result["confidence"].iloc[1] == "low"


# --- check_sources ---

class TestCheckSources:
    @patch("pykabu_calendar.earnings.calendar.ALL_SOURCES")
    def test_returns_list_of_dicts(self, mock_sources):
        source1 = MagicMock()
        source1.check.return_value = {"name": "sbi", "ok": True, "rows": 50, "error": None}
        source2 = MagicMock()
        source2.check.return_value = {"name": "matsui", "ok": True, "rows": 100, "error": None}
        mock_sources.__iter__ = MagicMock(return_value=iter([source1, source2]))

        result = check_sources()
        assert len(result) == 2
        assert result[0]["name"] == "sbi"
        assert result[0]["ok"] is True

    @patch("pykabu_calendar.earnings.calendar.ALL_SOURCES")
    def test_handles_failed_source(self, mock_sources):
        source1 = MagicMock()
        source1.check.return_value = {"name": "sbi", "ok": False, "rows": 0, "error": "timeout"}
        mock_sources.__iter__ = MagicMock(return_value=iter([source1]))

        result = check_sources()
        assert result[0]["ok"] is False
        assert result[0]["error"] == "timeout"


# --- get_calendar with mocks ---

class TestGetCalendarUnit:
    @patch("pykabu_calendar.earnings.calendar.run_parallel")
    def test_empty_results_returns_empty_df(self, mock_parallel):
        """When all sources return empty, should return empty DataFrame."""
        mock_parallel.return_value = {
            "sbi": pd.DataFrame(columns=["code", "name", "datetime"]),
        }
        result = get_calendar("2026-02-10", include_ir=False, infer_from_history=False)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch("pykabu_calendar.earnings.calendar.run_parallel")
    def test_single_source_data(self, mock_parallel):
        """Single source with data should produce valid output."""
        source_df = _make_source_df(
            ["7203", "6758"],
            ["Toyota", "Sony"],
            ["2026-02-10 15:00", "2026-02-10 16:00"],
        )
        mock_parallel.return_value = {"matsui": source_df}

        result = get_calendar(
            "2026-02-10",
            sources=["matsui"],
            include_ir=False,
            infer_from_history=False,
        )
        assert len(result) == 2
        assert "datetime" in result.columns
        assert "confidence" in result.columns
        assert "during_trading_hours" in result.columns

    @patch("pykabu_calendar.earnings.calendar.run_parallel")
    def test_during_trading_hours_column(self, mock_parallel):
        """during_trading_hours should be True for 15:00 (afternoon session)."""
        source_df = _make_source_df(
            ["7203"],
            ["Toyota"],
            ["2026-02-10 15:00"],
        )
        mock_parallel.return_value = {"matsui": source_df}

        result = get_calendar(
            "2026-02-10",
            sources=["matsui"],
            include_ir=False,
            infer_from_history=False,
        )
        assert result["during_trading_hours"].iloc[0] == True

    @patch("pykabu_calendar.earnings.calendar.run_parallel")
    def test_during_trading_hours_false_for_after_close(self, mock_parallel):
        """during_trading_hours should be False for 16:00 (after close)."""
        source_df = _make_source_df(
            ["7203"],
            ["Toyota"],
            ["2026-02-10 16:00"],
        )
        mock_parallel.return_value = {"matsui": source_df}

        result = get_calendar(
            "2026-02-10",
            sources=["matsui"],
            include_ir=False,
            infer_from_history=False,
        )
        assert result["during_trading_hours"].iloc[0] == False

    @patch("pykabu_calendar.earnings.calendar.run_parallel")
    def test_unknown_source_ignored(self, mock_parallel):
        """Unknown source names should be skipped gracefully."""
        source_df = _make_source_df(["7203"], ["Toyota"], ["2026-02-10 15:00"])
        mock_parallel.return_value = {"matsui": source_df}

        result = get_calendar(
            "2026-02-10",
            sources=["matsui", "nonexistent"],
            include_ir=False,
            infer_from_history=False,
        )
        assert len(result) == 1
