# TASK-023: IR Page Parser

**Status**: done
**Priority**: high
**Depends on**: TASK-020, TASK-022

## Description
Parse earnings datetime from company IR pages.

## Acceptance Criteria
- [x] Create `ir/parser.py`
- [x] Function: `parse_earnings_datetime(url: str, code: str) -> datetime | None`
- [x] Rule-based parsing first:
  - Common date formats (YYYY/MM/DD, YYYY年MM月DD日)
  - Time patterns (HH:MM, 午後X時)
  - Table structures with "決算発表" keywords
- [x] LLM fallback for complex pages
- [x] Return confidence score with result
- [x] Test with 20+ real company IR pages

## Implementation Notes
- `EarningsInfo` dataclass with datetime, confidence, source, raw_text, has_time
- `ParseConfidence` enum: HIGH, MEDIUM, LOW
- Japanese date patterns:
  - `YYYY年MM月DD日`, `YYYY/MM/DD`, `YYYY-MM-DD`
  - `令和X年MM月DD日` (Reiwa era conversion)
- Japanese time patterns:
  - `HH:MM`, `HH時MM分`, `HH時`
  - `午後X時`, `午前X時` (AM/PM conversion)
- Context detection: Tables/divs with 決算発表, 決算短信, 業績発表 keywords
- Handles "未定" (undetermined) gracefully
- 33 unit tests covering all patterns and edge cases
