"""Backward-compat shim — imports from earnings.sources."""

from ..earnings.sources import get_matsui, get_sbi, get_tradersweb  # noqa: F401

__all__ = ["get_matsui", "get_tradersweb", "get_sbi"]
