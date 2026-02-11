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

For IR page discovery using Google Gemini:

```bash
pip install pykabu-calendar[llm]
```

### Parquet Export

For Parquet file export:

```bash
pip install pyarrow
```

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
