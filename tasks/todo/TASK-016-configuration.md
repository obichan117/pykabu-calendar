# TASK-016: Configuration System

**Status**: todo
**Priority**: medium

## Description
Implement configuration for LLM provider, timeouts, and other settings.

## Acceptance Criteria
- [ ] Create `config.py` or use module-level settings
- [ ] `configure(llm_provider="ollama", llm_model="llama3.2")`
- [ ] Configurable timeouts: per-company IR timeout (default 30s)
- [ ] Configurable parallel workers (default 5)
- [ ] Cache location setting
- [ ] Environment variable support for API keys (future Claude API)

## Notes
- Keep simple - avoid over-engineering
- Sensible defaults that work out of the box
