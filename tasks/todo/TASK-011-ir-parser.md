# TASK-011: IR Page Parser

**Status**: todo
**Priority**: medium

## Description
Parse official earnings datetime from discovered IR pages.

## Acceptance Criteria
- [ ] Create `official/ir_parser.py`
- [ ] Parse HTML tables, lists, or structured data
- [ ] Extract datetime (or just date if time not available)
- [ ] Detect if company publishes time or only date
- [ ] Set `publishes_time` flag: true/false
- [ ] Handle various date formats (Japanese, ISO, etc.)
- [ ] Return `time_official` column value

## Notes
- Many companies only publish date, not time
- Once we know policy, cache it to skip future checks
- Focus on extracting time - date is already accurate from other sources
