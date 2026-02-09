# TASK-016: Configuration System

**Status**: todo
**Priority**: medium
**Depends on**: None (can be done anytime)

## Description
Implement configuration for LLM provider, timeouts, and other settings.

## Acceptance Criteria
- [ ] Extend existing `config.py` with new settings
- [ ] LLM settings:
  - `llm_provider`: "gemini" (default), "anthropic", "openai", "ollama"
  - `llm_model`: Provider-specific model name
- [ ] Environment variables:
  - `GEMINI_API_KEY` (free tier)
  - `ANTHROPIC_API_KEY` (optional)
  - `OPENAI_API_KEY` (optional)
- [ ] Timeouts:
  - `ir_timeout`: Per-company IR discovery timeout (default 30s)
  - `llm_timeout`: LLM call timeout (default 60s)
- [ ] Parallel workers: `max_workers` (default 5)
- [ ] Cache settings:
  - `cache_dir`: Location (default `~/.pykabu_calendar/`)
  - `cache_ttl_days`: Cache invalidation (default 30)
- [ ] Function: `configure(**kwargs)` for runtime config

## Notes
- Keep simple - avoid over-engineering
- Sensible defaults that work out of the box
- Gemini free tier as default (no API key required for low usage)
