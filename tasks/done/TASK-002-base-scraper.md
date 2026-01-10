# TASK-002: Base Scraper Interface

**Status**: todo
**Priority**: high

## Description
Create the base scraper class that all calendar sources will inherit from.

## Acceptance Criteria
- [ ] Create `sources/base.py` with `BaseCalendarScraper` abstract class
- [ ] Define common interface: `get_calendar(target_date) -> DataFrame`
- [ ] Implement scraping priority: backend API -> requests/BS4 -> playwright -> selenium
- [ ] Add logging support
- [ ] Add timeout handling
- [ ] Define output columns: `code`, `date`, `time`, `type`

## Notes
- Reference existing `pykabu/core/calendar_scraper.py` for patterns
- Keep lightweight - no browser deps unless proven necessary
