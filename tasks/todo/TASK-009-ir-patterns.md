# TASK-009: IR Site Patterns

**Status**: todo
**Priority**: medium

## Description
Build a pattern library for discovering IR pages and earnings calendar URLs on company websites.

## Acceptance Criteria
- [ ] Create `official/patterns.py`
- [ ] Define common URL patterns (e.g., `/ir/`, `/investor/`, `/ir/calendar/`)
- [ ] Check `robots.txt` and sitemaps for hints
- [ ] Identify common IR platform providers (many companies use similar systems)
- [ ] Return list of candidate URLs to check
- [ ] Test with known companies (Toyota, Sony, SoftBank)

## Notes
- Start from `pykabutan.Ticker(code).profile.website`
- Many Japanese companies follow similar patterns
- Build pattern library from successful discoveries
