"""
pykabu-calendar - Japanese earnings calendar aggregator.

Usage:
    import pykabu_calendar as cal

    # Get calendar for a specific date (uses all sources by default)
    df = cal.get_calendar("2026-02-10")

    # Include IR discovery (on by default)
    df = cal.get_calendar("2026-02-10", include_ir=True)

    # Export to CSV / Parquet / SQLite
    cal.export_to_csv(df, "earnings.csv")
    cal.export_to_parquet(df, "earnings.parquet")
    cal.export_to_sqlite(df, "earnings.db")

    # Health check all sources
    cal.check_sources()
"""

from importlib.metadata import version as _get_version

from .earnings.calendar import get_calendar, check_sources
from .earnings.base import EarningsSource
from .core.io import export_to_csv, export_to_parquet, export_to_sqlite, load_from_sqlite
from .config import configure, get_settings
from .earnings.inference import get_past_earnings, infer_datetime, is_during_trading_hours
from .earnings.ir import discover_ir_page, parse_earnings_datetime

__version__ = _get_version("pykabu-calendar")

__all__ = [
    "__version__",
    # Configuration
    "configure",
    "get_settings",
    # Main API
    "get_calendar",
    "export_to_csv",
    "export_to_parquet",
    "export_to_sqlite",
    "load_from_sqlite",
    "check_sources",
    "EarningsSource",
    # IR discovery
    "discover_ir_page",
    "parse_earnings_datetime",
    # Inference
    "get_past_earnings",
    "infer_datetime",
    "is_during_trading_hours",
]
