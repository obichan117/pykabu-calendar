# TASK-010: IR Finder with LLM Fallback

**Status**: todo
**Priority**: medium

## Description
Implement IR page discovery logic with LLM fallback for edge cases.

## Acceptance Criteria
- [ ] Create `official/ir_finder.py`
- [ ] First: try known patterns from TASK-009
- [ ] If patterns fail: use LLM to analyze page and find IR link
- [ ] Timeout: 30 seconds per company
- [ ] Return `None` if not found (don't block)
- [ ] Cache successful paths for future use
- [ ] Feed accumulated patterns to LLM for better guessing

## Notes
- LLM is only used when pattern matching fails
- Best-effort approach - missing data is acceptable
- Focus on companies with trading-hour announcements (zaraba)
