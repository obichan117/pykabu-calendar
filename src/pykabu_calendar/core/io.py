"""Export and import utilities for calendar DataFrames."""

import logging
import sqlite3
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Columns that contain Python lists and need special serialization
_LIST_COLUMNS = ["candidate_datetimes", "past_datetimes"]


def export_to_csv(df: pd.DataFrame, path: str) -> None:
    """Export calendar DataFrame to CSV.

    List columns are serialized as semicolon-separated strings.
    Uses ``utf-8-sig`` encoding for Excel / Google Sheets compatibility.

    Args:
        df: Calendar DataFrame.
        path: Output file path.
    """
    export_df = df.copy()

    for col in _LIST_COLUMNS:
        if col in export_df.columns:
            export_df[col] = export_df[col].apply(
                lambda x: "; ".join(str(v) for v in x) if isinstance(x, list) else ""
            )

    export_df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"Exported {len(df)} entries to {path}")


def export_to_parquet(df: pd.DataFrame, path: str) -> None:
    """Export calendar DataFrame to Parquet.

    Args:
        df: Calendar DataFrame.
        path: Output file path (e.g. ``"earnings.parquet"``).
    """
    # Convert list columns to string for parquet compatibility
    export_df = df.copy()
    for col in _LIST_COLUMNS:
        if col in export_df.columns:
            export_df[col] = export_df[col].apply(
                lambda x: "; ".join(str(v) for v in x) if isinstance(x, list) else ""
            )

    export_df.to_parquet(path, index=False)
    logger.info(f"Exported {len(df)} entries to {path}")


def export_to_sqlite(
    df: pd.DataFrame,
    path: str,
    table: str = "earnings",
) -> None:
    """Export calendar DataFrame to SQLite.

    Args:
        df: Calendar DataFrame.
        path: Database file path (e.g. ``"earnings.db"``).
        table: Table name (default ``"earnings"``).
    """
    export_df = df.copy()
    for col in _LIST_COLUMNS:
        if col in export_df.columns:
            export_df[col] = export_df[col].apply(
                lambda x: "; ".join(str(v) for v in x) if isinstance(x, list) else ""
            )

    with sqlite3.connect(path) as conn:
        export_df.to_sql(table, conn, if_exists="replace", index=False)

    logger.info(f"Exported {len(df)} entries to {path}:{table}")


def load_from_sqlite(
    path: str,
    table: str = "earnings",
    date: Optional[str] = None,
) -> pd.DataFrame:
    """Load calendar DataFrame from SQLite.

    Args:
        path: Database file path.
        table: Table name (default ``"earnings"``).
        date: Optional date filter (``YYYY-MM-DD``). When provided, filters
              rows whose ``datetime`` column starts with this date string.

    Returns:
        Calendar DataFrame.
    """
    with sqlite3.connect(path) as conn:
        if date:
            query = f"SELECT * FROM [{table}] WHERE datetime LIKE ?"
            df = pd.read_sql(query, conn, params=(f"{date}%",))
        else:
            df = pd.read_sql(f"SELECT * FROM [{table}]", conn)

    logger.info(f"Loaded {len(df)} entries from {path}:{table}")
    return df
