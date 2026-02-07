# TASK-022: IR Page Discovery

**Status**: done
**Priority**: high
**Depends on**: TASK-020, TASK-021

## Description
Implement IR page discovery - find earnings calendar page from company website.

## Acceptance Criteria
- [x] Create `ir/discovery.py`
- [x] Function: `discover_ir_page(code: str) -> IRPageInfo | None`
- [x] Flow:
  1. Get company website from pykabutan
  2. Try candidate URLs from patterns
  3. If not found, fetch homepage and use LLM to find IR link
  4. Return IR page URL and type
- [x] Handle redirects, JS-heavy sites (use Playwright if needed)
- [x] Test with varied companies (large cap, small cap)

## Implementation Notes
- `IRPageInfo` dataclass with url, page_type, company_code, company_name, discovered_via
- `IRPageType` enum: CALENDAR, NEWS, LIBRARY, LANDING, UNKNOWN
- Discovery flow:
  1. Pattern matching (fastest) - tries ~25 common IR URL patterns
  2. Homepage link search (rule-based) - parses HTML for IR links
  3. LLM fallback (optional) - uses Gemini to find IR links
- `_detect_page_type()` classifies pages by URL and content
- `_find_ir_link_in_html()` searches for IR links using keywords
- 22 unit tests + 3 integration tests (slow, require network)
- Handles HEAD request fallback to GET (some servers block HEAD)
