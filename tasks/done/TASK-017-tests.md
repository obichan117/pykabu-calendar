# TASK-017: Tests

**Status**: todo
**Priority**: high

## Description
Create test suite with live scraping tests.

## Acceptance Criteria
- [ ] Create `tests/` directory with pytest setup
- [ ] Test fixtures: real stock codes (7203, 6758, 9984)
- [ ] Test each scraper individually with live data
- [ ] Test calendar merger with multiple sources
- [ ] Test historical inference
- [ ] Test official IR finder (with timeout)
- [ ] Test CSV export
- [ ] All tests use live data, no mocks

## Notes
- Tests will be slower due to live scraping
- Useful for catching site structure changes
- Run regularly to detect breakages
