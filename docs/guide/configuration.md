# Configuration

## Basic Configuration

```python
import pykabu_calendar as cal

cal.configure(
    llm_provider="ollama",
    llm_model="llama3.2",
    timeout=30,
    parallel_workers=5,
)
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `llm_provider` | `"ollama"` | LLM provider for IR discovery |
| `llm_model` | `"llama3.2"` | Model name |
| `timeout` | `30` | Seconds per company for IR discovery |
| `parallel_workers` | `5` | Concurrent IR verification workers |
| `cache_path` | `~/.pykabu_calendar/` | Location for cache files |

## LLM Providers

### Ollama (Default)

Free, local, private. Requires Ollama installed:

```bash
# Install
brew install ollama

# Pull model
ollama pull llama3.2

# Start server
ollama serve
```

```python
cal.configure(llm_provider="ollama", llm_model="llama3.2")
```

Available models:

- `llama3.2` (3B) - Fast, good for simple tasks
- `llama3.1` (8B) - Better reasoning
- `mistral` (7B) - Good balance
- `qwen2.5` (7B) - Strong for structured extraction

### Future: Claude API

Not yet implemented. Would require API key:

```python
cal.configure(
    llm_provider="anthropic",
    llm_model="claude-3-haiku",
    api_key="sk-..."
)
```

## Cache Location

Default: `~/.pykabu_calendar/`

Contents:

- `ir_cache.json` - Discovered IR URLs and policies

Override:

```python
cal.configure(cache_path="/path/to/custom/cache/")
```

## Environment Variables

For future API key support:

```bash
export ANTHROPIC_API_KEY="sk-..."
export OPENAI_API_KEY="sk-..."
```

## Default Sources

```python
# These are the defaults
cal.get_calendar(
    "2025-02-14",
    sources=["sbi", "matsui", "tradersweb"],
    infer_from_history=True,
    verify_official=False,
    eager=False,
)
```
