# TASK-024: IR Discovery Cache

**Status**: done
**Priority**: high
**Depends on**: TASK-022, TASK-023

## Description
Implement JSON cache for IR discoveries and parsing patterns.

## Acceptance Criteria
- [x] Create `ir/cache.py`
- [x] Cache location: `~/.pykabu_calendar/cache.json`
- [x] Cache per company:
  - `ir_url`: Discovered IR page URL
  - `ir_type`: Type of page (calendar, news, etc.)
  - `parse_pattern`: Successful parsing pattern (if rule-based)
  - `last_updated`: Timestamp
  - `success_count`: How many times parsing succeeded
- [x] Function: `get_cached(code: str) -> CacheEntry | None`
- [x] Function: `save_cache(code: str, entry: CacheEntry)`
- [x] Auto-save after successful discoveries
- [x] Support manual editing (human-readable JSON)
- [x] `eager=True` flag to bypass cache

## Implementation Notes
- `CacheEntry` dataclass with ir_url, ir_type, last_updated, discovered_via, parse_pattern, success_count, last_earnings_datetime
- `IRCache` class with get(), set(), delete(), clear(), clear_expired(), list_all(), stats()
- Human-readable JSON format with indentation
- Cache invalidation via `is_expired(ttl_days)` method
- `ignore_expired` flag to bypass TTL check (for eager mode)
- Convenience functions: `get_cache()`, `get_cached()`, `save_cache()`
- 21 unit tests covering all functionality
