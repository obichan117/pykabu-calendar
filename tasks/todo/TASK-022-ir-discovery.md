# TASK-022: IR Page Discovery

**Status**: todo
**Priority**: high
**Depends on**: TASK-020, TASK-021

## Description
Implement IR page discovery - find earnings calendar page from company website.

## Acceptance Criteria
- [ ] Create `ir/discovery.py`
- [ ] Function: `discover_ir_page(code: str) -> IRPageInfo | None`
- [ ] Flow:
  1. Get company website from pykabutan
  2. Try candidate URLs from patterns
  3. If not found, fetch homepage and use LLM to find IR link
  4. Return IR page URL and type
- [ ] Handle redirects, JS-heavy sites (use Playwright if needed)
- [ ] Test with varied companies (large cap, small cap)

## Notes
- Cache successful discoveries (see TASK-013)
- Some sites may require browser rendering
- Respect robots.txt
