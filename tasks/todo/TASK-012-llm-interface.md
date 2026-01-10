# TASK-012: LLM Interface

**Status**: todo
**Priority**: medium

## Description
Create model-agnostic LLM interface for IR discovery.

## Acceptance Criteria
- [ ] Create `llm/base.py` with abstract `LLMClient` interface
- [ ] Create `llm/ollama.py` with Ollama implementation
- [ ] Default model: `llama3.2` (configurable)
- [ ] Method: `find_ir_link(html_content, company_name) -> str | None`
- [ ] Method: `extract_earnings_datetime(html_content) -> datetime | None`
- [ ] Support few-shot learning from accumulated patterns
- [ ] Easy to swap to Claude API or other providers later

## Notes
- Keep interface simple - just text in, text out
- LLM calls are expensive - use only as fallback
- Model selection balances quality vs speed/cost
