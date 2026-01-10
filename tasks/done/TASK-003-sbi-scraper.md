# TASK-003: SBI Calendar Scraper

**Status**: todo
**Priority**: high

## Description
Implement SBI Securities earnings calendar scraper. This is the PRIMARY source.

## Acceptance Criteria
- [ ] Create `sources/sbi.py` with `SbiCalendarScraper` class
- [ ] First attempt: find backend API via network inspection
- [ ] Fallback: requests + BeautifulSoup scraping
- [ ] Last resort: Selenium (only if JS required)
- [ ] Parse columns: date, time, code, name, type, result, guidance, consensus
- [ ] Handle pagination ("100件" view, "次へ" button)
- [ ] Test with real dates and verify data matches website

## Notes
- URL pattern: `https://www.sbisec.co.jp/ETGate/?...&tl9-{YYYYMM}&tl10-{YYYYMMDD}`
- Reference: `pykabu/public_modules/sbi_calendar.py`
- Prioritize lightweight approach - check if API exists first
