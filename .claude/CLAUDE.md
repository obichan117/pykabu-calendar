# pykabu-calendar

Japanese earnings calendar aggregator. Scrapes multiple broker sites, company IR pages, and infers announcement times from historical patterns.

## Quick Start

```bash
# Setup
uv sync

# Run tests
uv run pytest

# Run tests (skip slow browser tests)
uv run pytest -k "not slow"

# Serve docs locally
uv run mkdocs serve

# Deploy docs
uv run mkdocs gh-deploy --force

# Publish to PyPI
uv build && uv run twine upload dist/* -u __token__ -p $PYPI_TOKEN
```

## Architecture

### Current (v0.4.0 - MVP Complete)

```
src/pykabu_calendar/
├── config.py              # Shared: USER_AGENT, TIMEOUT, HEADERS
├── core/
│   ├── fetch.py           # Generic fetch (requests, browser)
│   └── parse.py           # Generic parse (tables, regex, datetime)
├── sources/
│   ├── matsui/            # Matsui Securities
│   ├── tradersweb/        # Tradersweb
│   └── sbi/               # SBI Securities (requires Playwright)
├── calendar.py            # Aggregator: get_calendar(), export_to_csv()
└── inference.py           # Historical inference via pykabutan
```

### Target (Next Phase - IR Discovery)

```
src/pykabu_calendar/
├── ... (existing)
├── ir/                    # NEW - Company IR page discovery
│   ├── discovery.py       # Find IR pages from company website
│   ├── parser.py          # Rule-based datetime extraction
│   ├── patterns.py        # Common IR URL/HTML patterns
│   └── cache.py           # Cache discovered patterns (JSON)
├── llm/                   # NEW - LLM-assisted parsing
│   ├── base.py            # Abstract LLM interface
│   ├── gemini.py          # Free tier (primary)
│   └── anthropic.py       # Paid fallback
└── calendar.py            # Updated priority: ir > inferred > sbi > matsui > tradersweb
```

## Data Source Priority

```
1. ir_official      # Company IR page (most accurate, exact times)
2. inferred         # Historical patterns via pykabutan
3. sbi              # SBI Securities calendar
4. matsui           # Matsui Securities calendar
5. tradersweb       # Tradersweb calendar
```

## IR Discovery Flow

```
Company code (e.g., "7203")
    ↓
pykabutan → get company website URL
    ↓
Try common IR patterns (/ir/, /investor/, /ir/calendar/)
    ↓
If not found → LLM: "find IR page link in this HTML"
    ↓
Rule-based parsing for earnings datetime
    ↓
If fails → LLM: "extract earnings datetime from this page"
    ↓
Cache successful patterns for reuse
```

## LLM Priority

1. **Free API** - Gemini free tier (default)
2. **Paid API** - Claude/GPT (user provides key)
3. **Local** - Ollama (optional, user's machine)

## Key Files

| File | Purpose |
|------|---------|
| `calendar.py` | Main aggregator, merges sources, builds candidate datetimes |
| `inference.py` | Uses pykabutan for historical earnings patterns |
| `core/fetch.py` | `fetch()`, `fetch_browser()`, `fetch_browser_with_pagination()` |
| `core/parse.py` | `parse_table()`, `extract_regex()`, `to_datetime()` |
| `sources/*/config.py` | URLs, selectors - update here when sites change |
| `ir/discovery.py` | (Planned) Find company IR pages |
| `ir/cache.py` | (Planned) JSON cache for discovered patterns |
| `llm/base.py` | (Planned) Model-agnostic LLM interface |

## Output Schema

```python
df = cal.get_calendar("2026-02-10")
# Columns: code, name, datetime, candidate_datetimes,
#          ir_datetime,          # NEW - from company IR page
#          sbi_datetime, matsui_datetime, tradersweb_datetime,
#          inferred_datetime, past_datetimes
```

## Testing Notes

- Tests use **dynamic dates** (finds future date with earnings)
- Tradersweb blocks cloud IPs (Colab) - handled gracefully
- Browser tests marked with `@pytest.mark.slow`
- IR discovery tests should mock external sites

## Related Projects

- **vibe-trader** - Event backtesting uses this library for earnings dates
  - Spec: `/dev/vibe-trader/docs/specs/event-backtest.md`
