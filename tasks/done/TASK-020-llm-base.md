# TASK-020: LLM Base Interface

**Status**: done
**Priority**: high
**Depends on**: None

## Description
Create model-agnostic LLM interface for IR discovery and parsing.

## Acceptance Criteria
- [x] Create `llm/__init__.py`
- [x] Create `llm/base.py` with abstract `LLMClient` interface
- [x] Define methods:
  - `find_link(html: str, description: str) -> str | None`
  - `extract_datetime(html: str, context: str) -> datetime | None`
- [x] Create `llm/gemini.py` using free tier (primary)
- [x] Environment variable: `GEMINI_API_KEY`
- [x] Rate limiting and error handling
- [x] Test with simple examples

## Implementation Notes
- Used new `google-genai` SDK (replacing deprecated `google-generativeai`)
- Default model: `gemini-2.0-flash` (fast and free tier friendly)
- Rate limiting: 15 RPM with automatic throttling
- Tests: 17 unit tests + 3 integration tests (require API key)
