"""Backward-compat shim — imports from earnings.calendar and core.io."""

from .earnings.calendar import get_calendar  # noqa: F401
from .core.io import export_to_csv  # noqa: F401

__all__ = ["get_calendar", "export_to_csv"]
