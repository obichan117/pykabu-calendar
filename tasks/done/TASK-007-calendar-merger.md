# TASK-007: Calendar Merger

**Status**: todo
**Priority**: high

## Description
Implement logic to merge calendars from multiple sources into a single DataFrame with reconciled datetime.

## Acceptance Criteria
- [ ] Create `calendar.py` with merge logic
- [ ] Outer join all sources on `code`
- [ ] Keep individual time columns: `time_sbi`, `time_matsui`, etc.
- [ ] Merge time with priority: use first available (SBI > Matsui > Tradersweb)
- [ ] Create unified `datetime` column
- [ ] Track `datetime_source` - which source provided the time
- [ ] Handle conflicts gracefully

## Notes
- Reference: `pykabu/public_modules/earnings_calendar.py` `_merge_calendar()` method
- Use `combine_first()` pattern for merging columns
