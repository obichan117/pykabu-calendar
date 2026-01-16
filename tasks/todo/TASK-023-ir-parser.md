# TASK-023: IR Page Parser

**Status**: todo
**Priority**: high
**Depends on**: TASK-020, TASK-022

## Description
Parse earnings datetime from company IR pages.

## Acceptance Criteria
- [ ] Create `ir/parser.py`
- [ ] Function: `parse_earnings_datetime(url: str, code: str) -> datetime | None`
- [ ] Rule-based parsing first:
  - Common date formats (YYYY/MM/DD, YYYY年MM月DD日)
  - Time patterns (HH:MM, 午後X時)
  - Table structures with "決算発表" keywords
- [ ] LLM fallback for complex pages
- [ ] Return confidence score with result
- [ ] Test with 20+ real company IR pages

## Notes
- Save successful parsing patterns to cache
- Some companies don't publish exact times
- Handle "未定" (undetermined) gracefully
