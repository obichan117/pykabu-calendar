# Installation

## Basic Installation

```bash
pip install pykabu-calendar
```

Or with `uv`:

```bash
uv pip install pykabu-calendar
```

## Optional Dependencies

### LLM Support

For IR page discovery using local LLMs:

```bash
pip install pykabu-calendar[llm]
```

This installs Ollama client. You'll also need Ollama running locally:

```bash
# Install Ollama (macOS)
brew install ollama

# Pull a model
ollama pull llama3.2

# Start Ollama server
ollama serve
```

### Browser Support

If some calendar sites require JavaScript rendering:

```bash
pip install pykabu-calendar[browser]
```

!!! note
    Browser dependencies are only added if needed. The library tries lightweight approaches first.

### Development

For contributing or running tests:

```bash
pip install pykabu-calendar[dev]
```

### Everything

```bash
pip install pykabu-calendar[all]
```

## From Source

```bash
git clone https://github.com/obichan117/pykabu-calendar.git
cd pykabu-calendar
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Requirements

- Python 3.11+
- macOS, Linux, or Windows
