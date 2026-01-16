# TASK-024: IR Discovery Cache

**Status**: todo
**Priority**: high
**Depends on**: TASK-022, TASK-023

## Description
Implement JSON cache for IR discoveries and parsing patterns.

## Acceptance Criteria
- [ ] Create `ir/cache.py`
- [ ] Cache location: `~/.pykabu_calendar/cache.json`
- [ ] Cache per company:
  - `ir_url`: Discovered IR page URL
  - `ir_type`: Type of page (calendar, news, etc.)
  - `parse_pattern`: Successful parsing pattern (if rule-based)
  - `last_updated`: Timestamp
  - `success_count`: How many times parsing succeeded
- [ ] Function: `get_cached(code: str) -> CacheEntry | None`
- [ ] Function: `save_cache(code: str, entry: CacheEntry)`
- [ ] Auto-save after successful discoveries
- [ ] Support manual editing (human-readable JSON)
- [ ] `eager=True` flag to bypass cache

## Notes
- Merge with TASK-013 (same concept)
- Allow users to share/export cache files
- Invalidate after X days (configurable)
