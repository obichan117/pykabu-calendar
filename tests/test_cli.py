"""
Unit tests for CLI (click commands).

All tests use CliRunner and mocks — no network required.
"""

from unittest.mock import patch, MagicMock

import pandas as pd
from click.testing import CliRunner

from pykabu_calendar.cli import main


runner = CliRunner()


def test_version():
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "pykabu-calendar" in result.output


def test_config():
    result = runner.invoke(main, ["config"])
    assert result.exit_code == 0
    assert "timeout" in result.output
    assert "max_workers" in result.output


def test_check_ok():
    mock_results = [
        {"name": "sbi", "ok": True, "rows": 42, "error": None},
        {"name": "matsui", "ok": True, "rows": 30, "error": None},
        {"name": "tradersweb", "ok": False, "rows": 0, "error": "timeout"},
    ]
    with patch("pykabu_calendar.cli.cal.check_sources", return_value=mock_results):
        result = runner.invoke(main, ["check"])
    assert result.exit_code == 0
    assert "sbi" in result.output
    assert "ok" in result.output
    assert "FAIL" in result.output
    assert "timeout" in result.output


def _sample_df():
    return pd.DataFrame({
        "code": ["7203", "6758"],
        "name": ["Toyota", "Sony"],
        "datetime": [pd.Timestamp("2026-02-10 15:00"), pd.Timestamp("2026-02-10 12:00")],
        "confidence": ["high", "medium"],
        "during_trading_hours": [True, False],
    })


def test_calendar_table():
    with patch("pykabu_calendar.cli.cal.get_calendar", return_value=_sample_df()):
        result = runner.invoke(main, ["calendar", "2026-02-10"])
    assert result.exit_code == 0
    assert "7203" in result.output
    assert "Toyota" in result.output


def test_calendar_csv():
    with patch("pykabu_calendar.cli.cal.get_calendar", return_value=_sample_df()):
        result = runner.invoke(main, ["calendar", "2026-02-10", "-f", "csv"])
    assert result.exit_code == 0
    assert "code,name" in result.output
    assert "7203" in result.output


def test_calendar_json():
    with patch("pykabu_calendar.cli.cal.get_calendar", return_value=_sample_df()):
        result = runner.invoke(main, ["calendar", "2026-02-10", "-f", "json"])
    assert result.exit_code == 0
    assert '"code":"7203"' in result.output or '"code": "7203"' in result.output


def test_calendar_output_csv(tmp_path):
    out = tmp_path / "out.csv"
    with patch("pykabu_calendar.cli.cal.get_calendar", return_value=_sample_df()):
        with patch("pykabu_calendar.cli.cal.export_to_csv") as mock_export:
            result = runner.invoke(main, ["calendar", "2026-02-10", "-o", str(out)])
    assert result.exit_code == 0
    mock_export.assert_called_once()
    assert "Exported 2 rows" in result.output


def test_calendar_output_parquet(tmp_path):
    out = tmp_path / "out.parquet"
    with patch("pykabu_calendar.cli.cal.get_calendar", return_value=_sample_df()):
        with patch("pykabu_calendar.cli.cal.export_to_parquet") as mock_export:
            result = runner.invoke(main, ["calendar", "2026-02-10", "-o", str(out)])
    assert result.exit_code == 0
    mock_export.assert_called_once()


def test_calendar_output_db(tmp_path):
    out = tmp_path / "out.db"
    with patch("pykabu_calendar.cli.cal.get_calendar", return_value=_sample_df()):
        with patch("pykabu_calendar.cli.cal.export_to_sqlite") as mock_export:
            result = runner.invoke(main, ["calendar", "2026-02-10", "-o", str(out)])
    assert result.exit_code == 0
    mock_export.assert_called_once()


def test_calendar_options():
    with patch("pykabu_calendar.cli.cal.get_calendar", return_value=_sample_df()) as mock_cal:
        result = runner.invoke(main, [
            "calendar", "2026-02-10",
            "--no-ir", "--no-infer", "--sources", "sbi,matsui",
        ])
    assert result.exit_code == 0
    mock_cal.assert_called_once_with(
        "2026-02-10",
        sources=["sbi", "matsui"],
        include_ir=False,
        ir_eager=False,
        infer_from_history=False,
    )


def test_calendar_error():
    with patch("pykabu_calendar.cli.cal.get_calendar", side_effect=RuntimeError("boom")):
        result = runner.invoke(main, ["calendar", "2026-02-10"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_lookup():
    mock_past = [pd.Timestamp("2025-11-01 15:00"), pd.Timestamp("2025-08-01 15:00")]
    with patch("pykabu_calendar.cli.cal.get_past_earnings", return_value=mock_past):
        with patch(
            "pykabu_calendar.cli.cal.infer_datetime",
            return_value=(pd.Timestamp("2099-01-01 15:00"), "high", mock_past),
        ):
            result = runner.invoke(main, ["lookup", "7203"])
    assert result.exit_code == 0
    assert "7203" in result.output
    assert "15:00" in result.output
    assert "high" in result.output


def test_lookup_with_ir():
    mock_page = MagicMock()
    mock_page.url = "https://example.com/ir/"
    mock_page.page_type = "calendar"
    mock_page.discovered_via = "pattern"

    with patch("pykabu_calendar.cli.cal.get_past_earnings", return_value=[]):
        with patch(
            "pykabu_calendar.cli.cal.infer_datetime",
            return_value=(pd.NaT, "none", []),
        ):
            with patch("pykabu_calendar.cli.cal.discover_ir_page", return_value=mock_page):
                result = runner.invoke(main, ["lookup", "7203", "--ir"])
    assert result.exit_code == 0
    assert "https://example.com/ir/" in result.output


def test_lookup_no_past():
    with patch("pykabu_calendar.cli.cal.get_past_earnings", return_value=[]):
        with patch(
            "pykabu_calendar.cli.cal.infer_datetime",
            return_value=(pd.NaT, "none", []),
        ):
            result = runner.invoke(main, ["lookup", "9999"])
    assert result.exit_code == 0
    assert "No past announcements found" in result.output
