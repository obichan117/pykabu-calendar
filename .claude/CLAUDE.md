# pykabu-calendar

Japanese earnings calendar aggregator with official IR verification.

## Quick Start

```bash
# Setup
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run tests
pytest

# Build docs
mkdocs serve
```

## Project Overview

**Problem**: Japanese stock investors need accurate earnings announcement datetime. Multiple broker sites disagree, and knowing exact time matters for trading during market hours (zaraba).

**Solution**: Aggregate multiple calendar sources, infer from historical patterns, and optionally verify against official company IR pages.

## Accuracy Hierarchy

1. **Official company IR** (best, slow, optional)
2. **Historical pattern inference** (via pykabutan)
3. **SBI calendar** (primary public source)
4. **Supplementary calendars** (Matsui, Monex, Tradersweb)

## Public API

```python
import pykabu_calendar as cal

# Basic usage
df = cal.get_calendar(
    "2025-02-14",
    sources=["sbi", "matsui", "tradersweb"],
    infer_from_history=True,
    verify_official=False,
)

# With official IR verification (uses cache)
df = cal.get_calendar("2025-02-14", verify_official=True)

# Eager mode - refresh cached policies
df = cal.get_calendar("2025-02-14", verify_official=True, eager=True)

# Configure LLM for IR discovery
cal.configure(llm_provider="ollama", llm_model="llama3.2")
```

## Output Columns

| Column | Description |
|--------|-------------|
| `code` | Stock code (e.g., "7203") |
| `name` | Company name |
| `datetime` | Best guess datetime (merged) |
| `datetime_source` | Which source provided datetime |
| `time_sbi`, `time_matsui`, ... | Raw time from each source |
| `time_inferred` | Time guessed from historical patterns |
| `time_official` | Time from company IR (if verified) |
| `ir_url` | Cached IR page URL |
| `publishes_time` | true/false/unknown - company policy |
| `confidence` | official > inferred > scraped |

## Official IR Verification Logic

- **Only check if time is during trading hours** (9:00-11:30, 12:30-15:30)
- If time >= 15:30 → skip (doesn't matter for trading)
- Cache `ir_url` and `publishes_time` per company
- Timeout 30s per company, fail gracefully → return None
- `eager=True` ignores cache, re-checks all policies

## Scraping Strategy (priority order)

1. Backend API (if discoverable via network inspection)
2. requests + BeautifulSoup (lightweight)
3. Playwright (only if JS rendering required)
4. Selenium (last resort)

## LLM for IR Discovery

- Model-agnostic (default: Ollama with llama3.2)
- Used when pattern matching fails to find IR page
- Learns from accumulated successful paths over time
- Configure via `cal.configure(llm_provider="ollama", llm_model="...")`

## Storage

- **JSON**: IR path cache (`ir_cache.json`)
- **CSV**: Calendar results (Google Sheets compatible)

## Architecture

```
src/pykabu_calendar/
├── __init__.py
├── calendar.py          # Main EarningsCalendar class
├── sources/
│   ├── base.py          # Base scraper interface
│   ├── sbi.py           # SBI (primary)
│   ├── matsui.py        # Matsui (supplementary)
│   ├── monex.py         # Monex (supplementary)
│   └── tradersweb.py    # Tradersweb (supplementary)
├── official/
│   ├── ir_finder.py     # Discover IR earnings URL
│   ├── ir_parser.py     # Parse official earnings datetime
│   └── patterns.py      # Known IR site patterns
├── inference/
│   └── historical.py    # Infer time from past patterns
├── llm/
│   ├── base.py          # LLM interface
│   └── ollama.py        # Ollama implementation
└── utils/
    ├── cache.py         # IR path caching
    └── export.py        # CSV export
```

## Dependencies

**Required:**
- `pykabutan` - company data, historical earnings, website URL
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `pandas` - DataFrame handling
- `lxml` - fast HTML parser

**Optional (added only if needed):**
- `[browser]` - playwright/selenium (if JS rendering required)
- `[llm]` - ollama client

## Testing

- Always live scraping with real stock codes
- Test fixtures: 7203 (Toyota), 6758 (Sony), 9984 (SoftBank)
- No mocked responses

## Environment

- macOS on Apple Silicon (M1)
- Python 3.11+
- Use `uv` for package management

## Related Libraries

- `pykabutan` - kabutan.jp scraper (provides company data)
- Original `pykabu` codebase - reference implementation
