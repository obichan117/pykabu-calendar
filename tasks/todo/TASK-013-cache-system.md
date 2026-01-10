# TASK-013: Cache System

**Status**: todo
**Priority**: high

## Description
Implement caching for IR paths and company policies.

## Acceptance Criteria
- [ ] Create `utils/cache.py`
- [ ] Store in JSON format (human-readable, editable)
- [ ] Cache per company: `ir_url`, `publishes_time`, `ir_parse_format`
- [ ] Load cache on startup
- [ ] Save cache after discoveries
- [ ] Support manual edits (users can add paths they found)
- [ ] `eager=True` flag ignores cache for fresh discovery

## Notes
- Cache location: `~/.pykabu_calendar/ir_cache.json` or project-local
- Policies rarely change - cache is long-lived
- Allow users to share/export cache files
