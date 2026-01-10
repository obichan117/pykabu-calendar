# TASK-004: Matsui Calendar Scraper

**Status**: todo
**Priority**: medium

## Description
Implement Matsui Securities earnings calendar scraper (supplementary source).

## Acceptance Criteria
- [ ] Create `sources/matsui.py` with `MatsuiCalendarScraper` class
- [ ] First attempt: find backend API
- [ ] Fallback: requests + BeautifulSoup
- [ ] Parse columns: date, time, code, name, type
- [ ] Test with real dates

## Notes
- Reference: `pykabu/public_modules/matsui_calendar.py`
- Supplementary source - used to cross-check SBI data
