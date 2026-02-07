# TASK-021: IR URL Patterns Library

**Status**: done
**Priority**: high
**Depends on**: None

## Description
Build pattern library for common IR page URL structures.

## Acceptance Criteria
- [x] Create `ir/__init__.py`
- [x] Create `ir/patterns.py` with common URL patterns
- [x] Patterns to check:
  - `/ir/`, `/investor/`, `/investors/`
  - `/ir/calendar/`, `/ir/schedule/`
  - `/ir/library/`, `/ir/news/`
  - Common IR platforms (e.g., irbank providers)
- [x] Function: `get_candidate_urls(base_url: str) -> list[str]`
- [x] Test with 10+ known company websites

## Implementation Notes
- Uses `pykabutan.Ticker(code).profile.website` for base URLs
- Patterns include both English and Japanese paths (決算, 業績, etc.)
- `normalize_base_url()` handles URL normalization
- `is_known_ir_platform()` detects external IR platforms
- 20 unit tests + 1 integration test (slow, requires network)
- Tested with 10 major Japanese companies (Toyota, Sony, SoftBank, MUFG, Honda, NTT, Tokyo Electron, Ajinomoto, Hitachi, Takeda)
