"""Tests for core/parse.py — HTML parsing and data transformation."""

import pandas as pd
import pytest

from pykabu_calendar.core.parse import parse_table, extract_regex, to_datetime, combine_datetime


SIMPLE_TABLE = """
<html><body>
<table>
  <tr><th>Name</th><th>Code</th></tr>
  <tr><td>Toyota</td><td>7203</td></tr>
  <tr><td>Sony</td><td>6758</td></tr>
</table>
</body></html>
"""

TWO_TABLES = """
<html><body>
<table class="first"><tr><th>A</th></tr><tr><td>1</td></tr></table>
<table class="second"><tr><th>B</th></tr><tr><td>2</td></tr></table>
</body></html>
"""


class TestParseTable:
    """Tests for parse_table()."""

    def test_basic_table(self):
        df = parse_table(SIMPLE_TABLE)
        assert len(df) == 2
        assert "Name" in df.columns
        assert "Code" in df.columns

    def test_with_css_selector(self):
        df = parse_table(TWO_TABLES, selector="table.second")
        assert len(df) == 1
        assert "B" in df.columns

    def test_selector_not_found_returns_empty(self):
        df = parse_table(SIMPLE_TABLE, selector="table.missing")
        assert df.empty

    def test_index_selects_table(self):
        df = parse_table(TWO_TABLES, index=1)
        assert "B" in df.columns

    def test_index_out_of_range_returns_first(self):
        df = parse_table(TWO_TABLES, index=99)
        assert "A" in df.columns

    def test_no_table_returns_empty(self):
        df = parse_table("<html><body><p>No table</p></body></html>")
        assert df.empty

    def test_empty_html_returns_empty(self):
        df = parse_table("")
        assert df.empty


class TestExtractRegex:
    """Tests for extract_regex()."""

    def test_basic_extraction(self):
        s = pd.Series(["Toyota(7203)", "Sony(6758)"])
        result = extract_regex(s, r"\((\w+)\)")
        assert list(result) == ["7203", "6758"]

    def test_no_match_returns_nan(self):
        s = pd.Series(["NoMatch"])
        result = extract_regex(s, r"\((\w+)\)")
        assert pd.isna(result.iloc[0])

    def test_mixed_values(self):
        s = pd.Series(["Toyota(7203)", "NoMatch", "Sony(6758)"])
        result = extract_regex(s, r"\((\w+)\)")
        assert result.iloc[0] == "7203"
        assert pd.isna(result.iloc[1])
        assert result.iloc[2] == "6758"


class TestToDatetime:
    """Tests for to_datetime()."""

    def test_basic_conversion(self):
        s = pd.Series(["2026-02-10", "2026-02-11"])
        result = to_datetime(s)
        assert result.iloc[0] == pd.Timestamp("2026-02-10")

    def test_with_format(self):
        s = pd.Series(["10/02/2026"])
        result = to_datetime(s, format="%d/%m/%Y")
        assert result.iloc[0] == pd.Timestamp("2026-02-10")

    def test_coerce_invalid(self):
        s = pd.Series(["2026-02-10", "not-a-date"])
        result = to_datetime(s)
        assert pd.notna(result.iloc[0])
        assert pd.isna(result.iloc[1])


class TestCombineDatetime:
    """Tests for combine_datetime()."""

    def test_basic_combine(self):
        dates = pd.Series(["2026-02-10", "2026-02-11"])
        times = pd.Series(["15:00", "16:30"])
        result = combine_datetime(dates, times)
        assert result.iloc[0] == pd.Timestamp("2026-02-10 15:00")
        assert result.iloc[1] == pd.Timestamp("2026-02-11 16:30")

    def test_missing_time_gives_nat(self):
        dates = pd.Series(["2026-02-10"])
        times = pd.Series([None])
        result = combine_datetime(dates, times)
        assert pd.isna(result.iloc[0])

    def test_nan_time_gives_nat(self):
        dates = pd.Series(["2026-02-10", "2026-02-11"])
        times = pd.Series(["15:00", float("nan")])
        result = combine_datetime(dates, times)
        assert pd.notna(result.iloc[0])
        assert pd.isna(result.iloc[1])
