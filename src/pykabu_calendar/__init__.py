"""
pykabu-calendar - Japanese earnings calendar aggregator.

Usage:
    import pykabu_calendar as cal

    # Get calendar for a specific date (uses all sources by default)
    df = cal.get_calendar("2026-02-10")

    # Use specific sources only (faster, no browser needed)
    df = cal.get_calendar("2026-02-10", sources=["matsui", "tradersweb"])

    # Include IR discovery (on by default)
    df = cal.get_calendar("2026-02-10", include_ir=True)

    # Export to CSV
    cal.export_to_csv(df, "earnings.csv")
"""

from .calendar import get_calendar, export_to_csv
from .config import configure, get_settings
from .inference import get_past_earnings, infer_datetime, is_during_trading_hours
from .sources import get_matsui, get_sbi, get_tradersweb
from .ir import discover_ir_page, discover_ir_pages, parse_earnings_datetime

__version__ = "0.5.0"

__all__ = [
    # Configuration
    "configure",
    "get_settings",
    # Main API
    "get_calendar",
    "export_to_csv",
    # IR discovery
    "discover_ir_page",
    "discover_ir_pages",
    "parse_earnings_datetime",
    # Inference
    "get_past_earnings",
    "infer_datetime",
    "is_during_trading_hours",
    # Individual scrapers
    "get_matsui",
    "get_sbi",
    "get_tradersweb",
]
