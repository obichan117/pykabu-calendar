# TASK-014: CSV Export

**Status**: todo
**Priority**: high

## Description
Export calendar DataFrame to CSV for Google Sheets compatibility.

## Acceptance Criteria
- [ ] Create `utils/export.py`
- [ ] Export to CSV with proper encoding (UTF-8 with BOM for Excel)
- [ ] Include all columns: code, name, datetime, time_*, ir_url, publishes_time, etc.
- [ ] Support custom output path
- [ ] Optional: append to existing file vs overwrite

## Notes
- CSV is primary output format for sharing
- Must work with Google Sheets import
- Consider date/time formatting for Japanese locale
