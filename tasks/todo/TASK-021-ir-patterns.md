# TASK-021: IR URL Patterns Library

**Status**: todo
**Priority**: high
**Depends on**: None

## Description
Build pattern library for common IR page URL structures.

## Acceptance Criteria
- [ ] Create `ir/__init__.py`
- [ ] Create `ir/patterns.py` with common URL patterns
- [ ] Patterns to check:
  - `/ir/`, `/investor/`, `/investors/`
  - `/ir/calendar/`, `/ir/schedule/`
  - `/ir/library/`, `/ir/news/`
  - Common IR platforms (e.g., irbank providers)
- [ ] Function: `get_candidate_urls(base_url: str) -> list[str]`
- [ ] Test with 10+ known company websites

## Notes
- Start from `pykabutan.Ticker(code).profile.website`
- Many Japanese companies follow similar patterns
- Log successful patterns for future reference
