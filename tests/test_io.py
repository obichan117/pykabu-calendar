"""Tests for export/import IO utilities."""

import os

import pandas as pd
import pytest

from pykabu_calendar.core.io import (
    export_to_csv,
    export_to_parquet,
    export_to_sqlite,
    load_from_sqlite,
)

_has_pyarrow = False
try:
    import pyarrow  # noqa: F401
    _has_pyarrow = True
except ImportError:
    pass


@pytest.fixture
def sample_df():
    """Create a sample calendar DataFrame for testing."""
    return pd.DataFrame({
        "code": ["7203", "6758"],
        "name": ["Toyota", "Sony"],
        "datetime": pd.to_datetime(["2026-02-10 15:00", "2026-02-10 16:00"]),
        "candidate_datetimes": [
            ["2026-02-10 15:00", "2026-02-10 16:00"],
            ["2026-02-10 16:00"],
        ],
        "past_datetimes": [
            ["2025-02-10 15:00"],
            [],
        ],
    })


@pytest.fixture
def simple_df():
    """Create a simple DataFrame without list columns."""
    return pd.DataFrame({
        "code": ["7203"],
        "name": ["Toyota"],
        "datetime": pd.to_datetime(["2026-02-10 15:00"]),
    })


class TestExportToCsv:
    """Tests for export_to_csv."""

    def test_creates_file(self, sample_df, tmp_path):
        """Should create a CSV file."""
        path = str(tmp_path / "test.csv")
        export_to_csv(sample_df, path)
        assert os.path.exists(path)

    def test_list_columns_serialized(self, sample_df, tmp_path):
        """List columns should be serialized as semicolon-separated."""
        path = str(tmp_path / "test.csv")
        export_to_csv(sample_df, path)
        result = pd.read_csv(path)
        assert ";" in str(result["candidate_datetimes"].iloc[0])

    def test_roundtrip_shape(self, sample_df, tmp_path):
        """CSV should preserve row count."""
        path = str(tmp_path / "test.csv")
        export_to_csv(sample_df, path)
        result = pd.read_csv(path)
        assert len(result) == len(sample_df)


@pytest.mark.skipif(not _has_pyarrow, reason="pyarrow not installed")
class TestExportToParquet:
    """Tests for export_to_parquet."""

    def test_creates_file(self, simple_df, tmp_path):
        """Should create a Parquet file."""
        path = str(tmp_path / "test.parquet")
        export_to_parquet(simple_df, path)
        assert os.path.exists(path)

    def test_roundtrip(self, simple_df, tmp_path):
        """Parquet roundtrip should preserve data."""
        path = str(tmp_path / "test.parquet")
        export_to_parquet(simple_df, path)
        result = pd.read_parquet(path)
        assert len(result) == len(simple_df)
        assert list(result.columns) == list(simple_df.columns)

    def test_list_columns_handled(self, sample_df, tmp_path):
        """List columns should be serialized for parquet."""
        path = str(tmp_path / "test.parquet")
        export_to_parquet(sample_df, path)
        result = pd.read_parquet(path)
        assert len(result) == len(sample_df)


class TestExportToSqlite:
    """Tests for export_to_sqlite."""

    def test_creates_file(self, simple_df, tmp_path):
        """Should create a SQLite file."""
        path = str(tmp_path / "test.db")
        export_to_sqlite(simple_df, path)
        assert os.path.exists(path)

    def test_custom_table_name(self, simple_df, tmp_path):
        """Should support custom table names."""
        path = str(tmp_path / "test.db")
        export_to_sqlite(simple_df, path, table="my_table")
        result = load_from_sqlite(path, table="my_table")
        assert len(result) == len(simple_df)


class TestLoadFromSqlite:
    """Tests for load_from_sqlite."""

    def test_roundtrip(self, simple_df, tmp_path):
        """SQLite roundtrip should preserve data."""
        path = str(tmp_path / "test.db")
        export_to_sqlite(simple_df, path)
        result = load_from_sqlite(path)
        assert len(result) == len(simple_df)
        assert "code" in result.columns
        assert "name" in result.columns

    def test_date_filter(self, tmp_path):
        """Should filter by date when provided."""
        df = pd.DataFrame({
            "code": ["7203", "6758"],
            "name": ["Toyota", "Sony"],
            "datetime": pd.to_datetime(["2026-02-10 15:00", "2026-02-11 16:00"]),
        })
        path = str(tmp_path / "test.db")
        export_to_sqlite(df, path)

        result = load_from_sqlite(path, date="2026-02-10")
        assert len(result) == 1
        assert result.iloc[0]["code"] == "7203"

    def test_list_columns_roundtrip(self, sample_df, tmp_path):
        """List columns should survive SQLite roundtrip as strings."""
        path = str(tmp_path / "test.db")
        export_to_sqlite(sample_df, path)
        result = load_from_sqlite(path)
        assert len(result) == len(sample_df)
