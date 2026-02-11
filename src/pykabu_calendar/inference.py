"""Backward-compat shim — imports from earnings.inference."""

from .earnings.inference import (  # noqa: F401
    get_past_earnings,
    infer_datetime,
    is_during_trading_hours,
)

__all__ = ["get_past_earnings", "infer_datetime", "is_during_trading_hours"]
