"""
pykabu-calendar - Japanese earnings calendar aggregator.

Usage:
    import pykabu_calendar as cal

    # Get calendar for a specific date
    df = cal.get_calendar("2026-02-10")

    # With SBI (requires Playwright)
    df = cal.get_calendar("2026-02-10", include_sbi=True)

    # Export to CSV
    cal.export_to_csv(df, "earnings.csv")
"""

from .calendar import get_calendar, export_to_csv
from .inference import get_past_earnings, infer_datetime, is_during_trading_hours
from .scrapers import fetch_matsui, fetch_sbi, fetch_tradersweb

__version__ = "0.2.0"

__all__ = [
    # Main API
    "get_calendar",
    "export_to_csv",
    # Inference
    "get_past_earnings",
    "infer_datetime",
    "is_during_trading_hours",
    # Individual scrapers
    "fetch_matsui",
    "fetch_sbi",
    "fetch_tradersweb",
]
