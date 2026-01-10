"""
Export utilities for calendar data.
"""

import logging
from pathlib import Path
from typing import Union

import pandas as pd

logger = logging.getLogger(__name__)


def export_to_csv(
    df: pd.DataFrame,
    path: Union[str, Path],
    encoding: str = "utf-8-sig",
    include_bom: bool = True,
) -> Path:
    """
    Export calendar DataFrame to CSV file.

    Uses UTF-8 with BOM by default for Excel/Google Sheets compatibility
    with Japanese characters.

    Args:
        df: Calendar DataFrame to export
        path: Output file path
        encoding: File encoding (default: utf-8-sig for BOM)
        include_bom: Whether to include BOM (default: True)

    Returns:
        Path to the created file
    """
    path = Path(path)

    # Use utf-8-sig for BOM, plain utf-8 otherwise
    if include_bom and encoding == "utf-8":
        encoding = "utf-8-sig"

    # Export
    df.to_csv(path, index=False, encoding=encoding)
    logger.info(f"Exported {len(df)} entries to {path}")

    return path


def format_for_google_sheets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format DataFrame for Google Sheets import.

    Ensures dates and times are in formats that Google Sheets recognizes.

    Args:
        df: Calendar DataFrame

    Returns:
        Formatted DataFrame
    """
    df = df.copy()

    # Format datetime column
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"]).dt.strftime("%Y-%m-%d %H:%M")

    # Format date column
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    return df
