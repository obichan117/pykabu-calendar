# TASK-005: Monex Calendar Scraper

**Status**: todo
**Priority**: low

## Description
Implement Monex Securities earnings calendar scraper (supplementary source).

## Acceptance Criteria
- [ ] Create `sources/monex.py` with `MonexCalendarScraper` class
- [ ] First attempt: find backend API
- [ ] Fallback: requests + BeautifulSoup
- [ ] Parse columns: date, time, code, name, type
- [ ] Test with real dates

## Notes
- Reference: `pykabu/public_modules/monex_calendar.py`
- Note: Monex calendar is often a subset of SBI - may have lower priority
