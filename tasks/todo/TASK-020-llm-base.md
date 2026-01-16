# TASK-020: LLM Base Interface

**Status**: todo
**Priority**: high
**Depends on**: None

## Description
Create model-agnostic LLM interface for IR discovery and parsing.

## Acceptance Criteria
- [ ] Create `llm/__init__.py`
- [ ] Create `llm/base.py` with abstract `LLMClient` interface
- [ ] Define methods:
  - `find_link(html: str, description: str) -> str | None`
  - `extract_datetime(html: str, context: str) -> datetime | None`
- [ ] Create `llm/gemini.py` using free tier (primary)
- [ ] Environment variable: `GEMINI_API_KEY`
- [ ] Rate limiting and error handling
- [ ] Test with simple examples

## Notes
- Reference vibe-trader's `apps/engine/app/ai/gemini_provider.py` for patterns
- Keep interface simple - text in, structured out
- Gemini free tier: 15 RPM, 1M TPD
