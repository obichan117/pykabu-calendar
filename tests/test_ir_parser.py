"""Tests for IR page parser module."""

import pytest
from datetime import datetime, time
from unittest.mock import Mock, patch

from pykabu_calendar.earnings.ir import (
    EarningsInfo,
    ParseConfidence,
    parse_earnings_datetime,
    parse_earnings_from_html,
)
from pykabu_calendar.earnings.ir.parser import (
    _parse_japanese_date,
    _parse_japanese_time,
    _has_undetermined_marker,
    _find_earnings_context,
    _parse_context_rule_based,
)
from bs4 import BeautifulSoup


class TestEarningsInfo:
    """Tests for EarningsInfo dataclass."""

    def test_basic_creation(self):
        """Test creating EarningsInfo."""
        dt = datetime(2025, 2, 14, 15, 0)
        info = EarningsInfo(
            datetime=dt,
            confidence=ParseConfidence.HIGH,
            source="rule",
        )
        assert info.datetime == dt
        assert info.confidence == ParseConfidence.HIGH
        assert info.source == "rule"
        assert info.has_time is True

    def test_str_representation(self):
        """Test string representation."""
        info = EarningsInfo(
            datetime=datetime(2025, 2, 14, 15, 0),
            confidence=ParseConfidence.HIGH,
            source="rule",
        )
        str_repr = str(info)
        assert "2025-02-14" in str_repr
        assert "high" in str_repr


class TestParseConfidence:
    """Tests for ParseConfidence enum."""

    def test_all_levels(self):
        """Test all confidence levels exist."""
        assert ParseConfidence.HIGH.value == "high"
        assert ParseConfidence.MEDIUM.value == "medium"
        assert ParseConfidence.LOW.value == "low"


class TestParseJapaneseDate:
    """Tests for _parse_japanese_date function."""

    def test_kanji_format(self):
        """Test parsing 2025年2月14日 format."""
        dt, text = _parse_japanese_date("決算発表日: 2025年2月14日")
        assert dt == datetime(2025, 2, 14)
        assert "2025年2月14日" in text

    def test_kanji_format_padded(self):
        """Test parsing 2025年02月14日 format."""
        dt, text = _parse_japanese_date("2025年02月14日 15:00")
        assert dt == datetime(2025, 2, 14)

    def test_slash_format(self):
        """Test parsing 2025/2/14 format."""
        dt, text = _parse_japanese_date("発表予定 2025/2/14")
        assert dt == datetime(2025, 2, 14)

    def test_iso_format(self):
        """Test parsing 2025-02-14 format."""
        dt, text = _parse_japanese_date("Date: 2025-02-14")
        assert dt == datetime(2025, 2, 14)

    def test_reiwa_format(self):
        """Test parsing 令和7年2月14日 format."""
        dt, text = _parse_japanese_date("令和7年2月14日")
        assert dt == datetime(2025, 2, 14)  # Reiwa 7 = 2025

    def test_no_date(self):
        """Test handling text without date."""
        dt, text = _parse_japanese_date("No date here")
        assert dt is None
        assert text is None

    def test_invalid_date(self):
        """Test handling invalid date values."""
        dt, text = _parse_japanese_date("2025年13月45日")  # Invalid month/day
        assert dt is None


class TestParseJapaneseTime:
    """Tests for _parse_japanese_time function."""

    def test_colon_format(self):
        """Test parsing 15:00 format."""
        t, text = _parse_japanese_time("発表時刻 15:00")
        assert t == time(15, 0)

    def test_kanji_format(self):
        """Test parsing 15時00分 format."""
        t, text = _parse_japanese_time("15時00分に発表")
        assert t == time(15, 0)

    def test_kanji_hour_only(self):
        """Test parsing 15時 format."""
        t, text = _parse_japanese_time("15時発表予定")
        assert t == time(15, 0)

    def test_pm_format(self):
        """Test parsing 午後3時 format."""
        t, text = _parse_japanese_time("午後3時に発表")
        assert t == time(15, 0)

    def test_pm_with_minutes(self):
        """Test parsing 午後3時30分 format."""
        t, text = _parse_japanese_time("午後3時30分")
        assert t == time(15, 30)

    def test_am_format(self):
        """Test parsing 午前11時 format."""
        t, text = _parse_japanese_time("午前11時発表")
        assert t == time(11, 0)

    def test_no_time(self):
        """Test handling text without time."""
        t, text = _parse_japanese_time("No time here")
        assert t is None


class TestHasUndeterminedMarker:
    """Tests for _has_undetermined_marker function."""

    def test_mitei(self):
        """Test detecting 未定."""
        assert _has_undetermined_marker("発表時刻: 未定")

    def test_tbd(self):
        """Test detecting TBD."""
        assert _has_undetermined_marker("Time: TBD")

    def test_no_marker(self):
        """Test when no undetermined marker."""
        assert not _has_undetermined_marker("15:00")


class TestFindEarningsContext:
    """Tests for _find_earnings_context function."""

    def test_finds_table_context(self):
        """Test finding context from table with earnings keywords."""
        html = """
        <html><body>
        <table>
            <tr><td>決算発表</td><td>2025年2月14日</td><td>15:00</td></tr>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        contexts = _find_earnings_context(soup)
        assert len(contexts) > 0
        assert any("2025年2月14日" in ctx for ctx in contexts)

    def test_finds_div_context(self):
        """Test finding context from div with earnings keywords."""
        html = """
        <html><body>
        <div>決算発表予定日: 2025年2月14日 15:00</div>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        contexts = _find_earnings_context(soup)
        assert len(contexts) > 0

    def test_finds_by_code(self):
        """Test finding context by stock code."""
        html = """
        <html><body>
        <p>7203 トヨタ自動車 2025年2月14日</p>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        contexts = _find_earnings_context(soup, code="7203")
        assert len(contexts) > 0
        assert any("7203" in ctx for ctx in contexts)


class TestParseContextRuleBased:
    """Tests for _parse_context_rule_based function."""

    def test_full_datetime(self):
        """Test parsing full datetime."""
        result = _parse_context_rule_based("決算発表 2025年2月14日 15:00")
        assert result is not None
        assert result.datetime == datetime(2025, 2, 14, 15, 0)
        assert result.confidence == ParseConfidence.HIGH
        assert result.has_time is True

    def test_date_only(self):
        """Test parsing date without time."""
        result = _parse_context_rule_based("決算発表 2025年2月14日")
        assert result is not None
        assert result.datetime.date() == datetime(2025, 2, 14).date()
        assert result.confidence == ParseConfidence.MEDIUM
        assert result.has_time is False

    def test_undetermined_time(self):
        """Test parsing with undetermined time marker."""
        result = _parse_context_rule_based("2025年2月14日 時刻未定")
        assert result is not None
        assert result.datetime.date() == datetime(2025, 2, 14).date()
        assert result.has_time is False

    def test_no_date(self):
        """Test handling text without date."""
        result = _parse_context_rule_based("決算発表予定")
        assert result is None


class TestParseEarningsFromHtml:
    """Tests for parse_earnings_from_html function."""

    def test_parses_table(self):
        """Test parsing from table HTML."""
        html = """
        <html><body>
        <table>
            <tr><th>イベント</th><th>日付</th><th>時刻</th></tr>
            <tr><td>決算発表</td><td>2025年2月14日</td><td>15:00</td></tr>
        </table>
        </body></html>
        """
        result = parse_earnings_from_html(html, use_llm_fallback=False)
        assert result is not None
        assert result.datetime == datetime(2025, 2, 14, 15, 0)
        assert result.source == "rule"

    def test_parses_paragraph(self):
        """Test parsing from paragraph HTML."""
        html = """
        <html><body>
        <p>2025年2月14日(金) 15:00に決算発表を予定しています。</p>
        </body></html>
        """
        result = parse_earnings_from_html(html, use_llm_fallback=False)
        assert result is not None
        assert result.datetime == datetime(2025, 2, 14, 15, 0)

    def test_no_earnings_info(self):
        """Test handling HTML without earnings info."""
        html = "<html><body><p>Welcome to our website.</p></body></html>"
        result = parse_earnings_from_html(html, use_llm_fallback=False)
        assert result is None

    def test_with_llm_fallback(self):
        """Test LLM fallback when rule-based fails."""
        html = "<html><body><p>No clear date format here.</p></body></html>"

        mock_llm = Mock()
        mock_llm.extract_datetime.return_value = datetime(2025, 2, 14, 15, 0)

        result = parse_earnings_from_html(
            html, llm_client=mock_llm, use_llm_fallback=True
        )
        assert result is not None
        assert result.source == "llm"


class TestParseEarningsDatetime:
    """Tests for parse_earnings_datetime function."""

    @patch("pykabu_calendar.earnings.ir.parser.fetch_safe")
    def test_parses_from_url(self, mock_fetch):
        """Test parsing from URL."""
        mock_fetch.return_value = """
        <html><body>
        <div>決算発表: 2025年2月14日 15:00</div>
        </body></html>
        """

        result = parse_earnings_datetime(
            "https://example.com/ir/", use_llm_fallback=False
        )
        assert result is not None
        assert result.datetime == datetime(2025, 2, 14, 15, 0)

    @patch("pykabu_calendar.earnings.ir.parser.fetch_safe")
    def test_handles_fetch_failure(self, mock_fetch):
        """Test handling fetch failure."""
        mock_fetch.return_value = None

        result = parse_earnings_datetime(
            "https://example.com/ir/", use_llm_fallback=False
        )
        assert result is None


@pytest.mark.slow
class TestParseEarningsIntegration:
    """Integration tests for parsing real IR pages."""

    def test_various_date_formats(self):
        """Test parsing various Japanese date formats."""
        test_cases = [
            ("2025年2月14日 15:00", datetime(2025, 2, 14, 15, 0)),
            ("2025/02/14 午後3時", datetime(2025, 2, 14, 15, 0)),
            ("令和7年2月14日 15時00分", datetime(2025, 2, 14, 15, 0)),
        ]

        for text, expected in test_cases:
            html = f"<html><body><p>決算発表 {text}</p></body></html>"
            result = parse_earnings_from_html(html, use_llm_fallback=False)
            assert result is not None, f"Failed to parse: {text}"
            assert result.datetime == expected, f"Wrong result for: {text}"
