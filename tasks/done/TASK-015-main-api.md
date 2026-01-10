# TASK-015: Main Public API

**Status**: todo
**Priority**: high

## Description
Implement the main `get_calendar()` function that ties everything together.

## Acceptance Criteria
- [ ] Create main API in `calendar.py` or `__init__.py`
- [ ] `get_calendar(date, sources=["sbi", "matsui", "tradersweb"], infer_from_history=True, verify_official=False, eager=False)`
- [ ] Orchestrate: scrape sources -> merge -> infer -> verify official
- [ ] Skip official check if time >= 15:30 (not significant)
- [ ] Skip official check if `publishes_time=False` (unless eager)
- [ ] Return DataFrame with all columns
- [ ] `get_calendars(year_month, start_day)` for date ranges

## Notes
- This is the main entry point for users
- Should be simple to use with sensible defaults
- Verbose logging for debugging
