"""IR discovery module for finding company investor relations pages."""

from .patterns import get_candidate_urls, IR_PATH_PATTERNS, CALENDAR_PATH_PATTERNS
from .discovery import (
    IRPageInfo,
    IRPageType,
    discover_ir_page,
)
from .parser import (
    EarningsInfo,
    ParseConfidence,
    parse_earnings_datetime,
    parse_earnings_from_html,
)
from .cache import (
    CacheEntry,
    IRCache,
    get_cache,
    get_cached,
    save_cache,
)

__all__ = [
    # Patterns
    "get_candidate_urls",
    "IR_PATH_PATTERNS",
    "CALENDAR_PATH_PATTERNS",
    # Discovery
    "IRPageInfo",
    "IRPageType",
    "discover_ir_page",
    # Parser
    "EarningsInfo",
    "ParseConfidence",
    "parse_earnings_datetime",
    "parse_earnings_from_html",
    # Cache
    "CacheEntry",
    "IRCache",
    "get_cache",
    "get_cached",
    "save_cache",
]
