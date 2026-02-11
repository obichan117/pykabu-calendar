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
    _add_history,
    _add_ir,
    _get_ir_datetime,
    _merge_sources,
    _build_candidates,
    _compute_confidence,
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


# --- _compute_confidence ---

class TestComputeConfidence:
    """Direct tests for _compute_confidence function."""

    def test_ir_is_highest(self):
        assert _compute_confidence(pd.Timestamp("2026-02-10 15:00"), None, {}) == "highest"

    def test_nat_ir_is_not_highest(self):
        """pd.NaT should NOT be treated as valid IR datetime."""
        assert _compute_confidence(pd.NaT, None, {}) != "highest"

    def test_none_ir_is_not_highest(self):
        assert _compute_confidence(None, None, {}) != "highest"

    def test_inferred_matches_scraper_is_high(self):
        scrapers = {"sbi_datetime": pd.Timestamp("2026-02-10 15:00")}
        result = _compute_confidence(None, pd.Timestamp("2026-02-10 15:00"), scrapers)
        assert result == "high"

    def test_nat_inferred_not_high(self):
        """pd.NaT inferred should not trigger 'high' confidence."""
        scrapers = {"sbi_datetime": pd.Timestamp("2026-02-10 15:00")}
        result = _compute_confidence(None, pd.NaT, scrapers)
        assert result == "low"

    def test_two_scrapers_agree_is_high(self):
        scrapers = {
            "sbi_datetime": pd.Timestamp("2026-02-10 15:00"),
            "matsui_datetime": pd.Timestamp("2026-02-10 15:00"),
        }
        assert _compute_confidence(None, None, scrapers) == "high"

    def test_two_scrapers_disagree_is_medium(self):
        scrapers = {
            "sbi_datetime": pd.Timestamp("2026-02-10 15:00"),
            "matsui_datetime": pd.Timestamp("2026-02-10 16:00"),
        }
        assert _compute_confidence(None, None, scrapers) == "medium"

    def test_single_scraper_is_low(self):
        scrapers = {"sbi_datetime": pd.Timestamp("2026-02-10 15:00")}
        assert _compute_confidence(None, None, scrapers) == "low"

    def test_no_sources_is_low(self):
        assert _compute_confidence(None, None, {}) == "low"


# --- dtype consistency ---

class TestDtypeConsistency:
    def test_merge_sources_datetime_dtype(self):
        """All *_datetime columns should be datetime64 after merge."""
        data = {
            "sbi": _make_source_df(["7203"], ["Toyota"], ["2026-02-10 15:00"]),
            "matsui": _make_source_df(["6758"], ["Sony"], ["2026-02-10 16:00"]),
        }
        result = _merge_sources(data)
        assert pd.api.types.is_datetime64_any_dtype(result["sbi_datetime"])
        assert pd.api.types.is_datetime64_any_dtype(result["matsui_datetime"])

    def test_merge_sources_code_is_str(self):
        """Code column should be str after outer merge."""
        data = {
            "sbi": _make_source_df(["7203"], ["Toyota"], ["2026-02-10 15:00"]),
            "matsui": _make_source_df(["6758"], ["Sony"], ["2026-02-10 16:00"]),
        }
        result = _merge_sources(data)
        assert result["code"].dtype == object
        assert all(isinstance(c, str) for c in result["code"])

    def test_build_candidates_datetime_dtype(self):
        """Output datetime column should be datetime64, not object."""
        df = pd.DataFrame({
            "code": ["7203", "6758"],
            "sbi_datetime": [pd.Timestamp("2026-02-10 15:00"), pd.NaT],
            "matsui_datetime": [pd.NaT, pd.Timestamp("2026-02-10 16:00")],
        })
        result = _build_candidates(df)
        assert pd.api.types.is_datetime64_any_dtype(result["datetime"])

    def test_build_candidates_all_nat_datetime_dtype(self):
        """Even when all values are NaT, datetime should be datetime64."""
        df = pd.DataFrame({
            "code": ["7203"],
            "sbi_datetime": [pd.NaT],
        })
        result = _build_candidates(df)
        assert pd.api.types.is_datetime64_any_dtype(result["datetime"])

    def test_empty_result_datetime_dtypes(self):
        """Empty result should have correct datetime dtypes."""
        result = _empty_result()
        assert pd.api.types.is_datetime64_any_dtype(result["datetime"])
        assert pd.api.types.is_datetime64_any_dtype(result["ir_datetime"])
        assert pd.api.types.is_datetime64_any_dtype(result["inferred_datetime"])

    @patch("pykabu_calendar.earnings.calendar.run_parallel")
    def test_get_calendar_dtype_consistency(self, mock_parallel):
        """Full pipeline should produce consistent dtypes."""
        source_df = _make_source_df(
            ["7203", "6758"],
            ["Toyota", "Sony"],
            ["2026-02-10 15:00", None],
        )
        mock_parallel.return_value = {"matsui": source_df}

        result = get_calendar(
            "2026-02-10",
            sources=["matsui"],
            include_ir=False,
            infer_from_history=False,
        )
        assert pd.api.types.is_datetime64_any_dtype(result["datetime"])
        assert result["code"].dtype == object
        assert all(isinstance(c, str) for c in result["code"])


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


# --- _add_history ---

class TestAddHistory:
    """Unit tests for _add_history with mocked dependencies."""

    @patch("pykabu_calendar.earnings.calendar.run_parallel")
    def test_adds_columns(self, mock_parallel):
        """Should add inferred_datetime and past_datetimes columns."""
        mock_parallel.return_value = {
            "7203": ([pd.Timestamp("2025-11-01 15:00")], pd.Timestamp("2026-02-10 15:00")),
        }
        df = pd.DataFrame({"code": ["7203"], "sbi_datetime": [pd.Timestamp("2026-02-10 15:00")]})
        result = _add_history(df, "2026-02-10", infer=True)
        assert "inferred_datetime" in result.columns
        assert "past_datetimes" in result.columns
        assert result["inferred_datetime"].iloc[0] == pd.Timestamp("2026-02-10 15:00")

    @patch("pykabu_calendar.earnings.calendar.run_parallel")
    def test_no_infer(self, mock_parallel):
        """With infer=False, inferred_datetime should be NaT."""
        mock_parallel.return_value = {
            "7203": (None, pd.NaT),
        }
        df = pd.DataFrame({"code": ["7203"], "sbi_datetime": [pd.Timestamp("2026-02-10 15:00")]})
        result = _add_history(df, "2026-02-10", infer=False)
        assert pd.isna(result["inferred_datetime"].iloc[0])

    @patch("pykabu_calendar.earnings.calendar.run_parallel")
    def test_missing_code_in_results(self, mock_parallel):
        """Codes not in results should get NaT and None."""
        mock_parallel.return_value = {}
        df = pd.DataFrame({"code": ["9999"], "sbi_datetime": [pd.NaT]})
        result = _add_history(df, "2026-02-10", infer=True)
        assert pd.isna(result["inferred_datetime"].iloc[0])
        assert result["past_datetimes"].iloc[0] is None


# --- _add_ir ---

class TestAddIr:
    """Unit tests for _add_ir with mocked dependencies."""

    @patch("pykabu_calendar.earnings.calendar.run_parallel")
    def test_adds_ir_datetime_column(self, mock_parallel):
        """Should add ir_datetime column."""
        mock_parallel.return_value = {
            "7203": pd.Timestamp("2026-02-10 14:00"),
        }
        df = pd.DataFrame({"code": ["7203"], "sbi_datetime": [pd.Timestamp("2026-02-10 15:00")]})
        result = _add_ir(df)
        assert "ir_datetime" in result.columns
        assert result["ir_datetime"].iloc[0] == pd.Timestamp("2026-02-10 14:00")

    @patch("pykabu_calendar.earnings.calendar.run_parallel")
    def test_nat_for_missing(self, mock_parallel):
        """Codes not in results should get NaT."""
        mock_parallel.return_value = {}
        df = pd.DataFrame({"code": ["9999"], "sbi_datetime": [pd.NaT]})
        result = _add_ir(df)
        assert pd.isna(result["ir_datetime"].iloc[0])


# --- _get_ir_datetime ---

class TestGetIrDatetime:
    """Unit tests for _get_ir_datetime with mocked dependencies."""

    @patch("pykabu_calendar.earnings.calendar.get_cached")
    def test_returns_cached_datetime(self, mock_cached):
        """Should return cached datetime when available."""
        mock_entry = MagicMock()
        mock_entry.last_earnings_datetime = "2026-02-10 14:00"
        mock_cached.return_value = mock_entry

        result = _get_ir_datetime("7203")
        assert result == pd.Timestamp("2026-02-10 14:00")

    @patch("pykabu_calendar.earnings.calendar.save_cache")
    @patch("pykabu_calendar.earnings.calendar.parse_earnings_datetime")
    @patch("pykabu_calendar.earnings.calendar.discover_ir_page")
    @patch("pykabu_calendar.earnings.calendar.get_cached")
    def test_returns_nat_when_no_page(self, mock_cached, mock_discover, mock_parse, mock_save):
        """Should return NaT when no IR page found."""
        mock_cached.return_value = None
        mock_discover.return_value = None

        result = _get_ir_datetime("9999")
        assert pd.isna(result)
        mock_parse.assert_not_called()

    @patch("pykabu_calendar.earnings.calendar.save_cache")
    @patch("pykabu_calendar.earnings.calendar.parse_earnings_datetime")
    @patch("pykabu_calendar.earnings.calendar.discover_ir_page")
    @patch("pykabu_calendar.earnings.calendar.get_cached")
    def test_discovers_and_parses(self, mock_cached, mock_discover, mock_parse, mock_save):
        """Should discover page, parse datetime, and cache result."""
        mock_cached.return_value = None
        mock_page = MagicMock()
        mock_page.url = "https://example.com/ir/"
        mock_page.page_type = "calendar"
        mock_page.discovered_via = "pattern"
        mock_discover.return_value = mock_page

        mock_earnings = MagicMock()
        mock_earnings.datetime = "2026-02-10 14:00"
        mock_parse.return_value = mock_earnings

        result = _get_ir_datetime("7203", eager=True)
        assert result == pd.Timestamp("2026-02-10 14:00")
        mock_save.assert_called_once()
