"""Unit tests for SBI source internals (no network required)."""

import pandas as pd

from pykabu_calendar.earnings.sources.sbi import (
    build_api_params,
    extract_hash,
    _parse_jsonp,
    _build_dataframe,
)


class TestExtractHash:
    """Tests for hash extraction from SBI page HTML."""

    def test_extracts_valid_hash(self):
        """Should extract 40-char hex hash."""
        html = 'var url = "/api?hash=abcdef0123456789abcdef0123456789abcdef01&type=delay";'
        result = extract_hash(html)
        assert result == "abcdef0123456789abcdef0123456789abcdef01"

    def test_returns_none_when_no_hash(self):
        """Should return None when no hash found."""
        html = "<html><body>No hash here</body></html>"
        result = extract_hash(html)
        assert result is None

    def test_ignores_short_hex(self):
        """Should not match hex strings shorter than 40 chars."""
        html = 'hash=abcdef01'
        result = extract_hash(html)
        assert result is None


class TestBuildApiParams:
    """Tests for API parameter construction."""

    def test_builds_correct_params(self):
        """Should build correct params dict."""
        params = build_api_params("abc123" * 7 + "ab", "2026-02-10")
        assert params["hash"] == "abc123" * 7 + "ab"
        assert params["selectedDate"] == "20260210"
        assert params["type"] == "delay"
        assert params["callback"] == "cb"


class TestParseJsonp:
    """Tests for JSONP response parsing."""

    def test_parses_valid_jsonp(self):
        """Should parse valid JSONP body."""
        jsonp = 'cb({"body": [{"productCode": "7203", "productName": "Toyota", "time": "15:00"}]})'
        result = _parse_jsonp(jsonp)
        assert len(result) == 1
        assert result[0]["productCode"] == "7203"

    def test_returns_empty_on_no_body(self):
        """Should return empty list when no body array found."""
        result = _parse_jsonp("cb({no body here})")
        assert result == []

    def test_returns_empty_on_invalid_json(self):
        """Should return empty list on invalid JSON inside body."""
        result = _parse_jsonp('cb({"body": [invalid json]})')
        assert result == []

    def test_multiple_items(self):
        """Should parse multiple items."""
        jsonp = 'cb({"body": [{"productCode": "7203"}, {"productCode": "6758"}]})'
        result = _parse_jsonp(jsonp)
        assert len(result) == 2


class TestBuildDataframe:
    """Tests for DataFrame construction from API items."""

    def test_builds_basic_dataframe(self):
        """Should build DataFrame from items."""
        items = [
            {"productCode": "7203", "productName": "Toyota", "time": "15:00"},
            {"productCode": "6758", "productName": "Sony", "time": "16:00"},
        ]
        df = _build_dataframe(items, "2026-02-10")
        assert len(df) == 2
        assert list(df.columns) == ["code", "name", "datetime"]
        assert df["code"].iloc[0] == "7203"
        assert df["datetime"].iloc[0] == pd.Timestamp("2026-02-10 15:00")

    def test_skips_items_without_code(self):
        """Should skip items with empty productCode."""
        items = [
            {"productCode": "", "productName": "Unknown", "time": "15:00"},
            {"productCode": "7203", "productName": "Toyota", "time": "15:00"},
        ]
        df = _build_dataframe(items, "2026-02-10")
        assert len(df) == 1

    def test_nat_for_missing_time(self):
        """Should use NaT when time is not parseable."""
        items = [{"productCode": "7203", "productName": "Toyota", "time": ""}]
        df = _build_dataframe(items, "2026-02-10")
        assert pd.isna(df["datetime"].iloc[0])

    def test_returns_empty_for_no_valid_items(self):
        """Should return empty DataFrame when no valid items."""
        items = [{"productCode": "", "productName": "", "time": ""}]
        df = _build_dataframe(items, "2026-02-10")
        assert df.empty
