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

## Architecture (v0.5.0)

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
├── ir/                    # Company IR page discovery
│   ├── discovery.py       # Find IR pages from company website
│   ├── parser.py          # Rule-based datetime extraction + LLM fallback
│   ├── patterns.py        # Common IR URL/HTML patterns
│   └── cache.py           # Cache discovered patterns (JSON)
├── llm/                   # LLM-assisted parsing
│   ├── base.py            # Abstract LLM interface + get_default_client()
│   └── gemini.py          # Google Gemini free tier client
├── calendar.py            # Aggregator: get_calendar(), export_to_csv()
└── inference.py           # Historical inference via pykabutan
```

## Data Source Priority

```
1. ir_datetime      # Company IR page (most accurate, exact times)
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
If not found → search homepage for IR links (rule-based)
    ↓
If still not found → LLM: "find IR page link in this HTML"
    ↓
Rule-based parsing for earnings datetime
    ↓
If fails → LLM: "extract earnings datetime from this page"
    ↓
Cache successful patterns for reuse
```

## Key Files

| File | Purpose |
|------|---------|
| `calendar.py` | Main aggregator, merges sources, IR integration, candidate ranking |
| `inference.py` | Uses pykabutan for historical earnings patterns |
| `core/fetch.py` | `fetch()`, `fetch_browser()`, `fetch_browser_with_pagination()` |
| `core/parse.py` | `parse_table()`, `extract_regex()`, `to_datetime()`, `combine_datetime()` |
| `sources/*/config.py` | URLs, selectors - update here when sites change |
| `ir/discovery.py` | Find company IR pages (pattern → homepage → LLM) |
| `ir/parser.py` | Parse earnings datetime from IR pages (rule-based → LLM) |
| `ir/cache.py` | JSON cache at `~/.pykabu_calendar/ir_cache.json` |
| `llm/base.py` | Abstract `LLMClient` + `get_default_client()` singleton |
| `llm/gemini.py` | `GeminiClient` with rate limiting |

## Output Schema

```python
df = cal.get_calendar("2026-02-10")
# Columns: code, name, datetime, candidate_datetimes,
#          ir_datetime, sbi_datetime, matsui_datetime,
#          tradersweb_datetime, inferred_datetime, past_datetimes

# Disable IR for speed
df = cal.get_calendar("2026-02-10", include_ir=False)

# Force IR re-discovery (bypass cache)
df = cal.get_calendar("2026-02-10", ir_eager=True)
```

## Testing Notes

- Tests use **dynamic dates** (finds future date with earnings)
- Tradersweb blocks cloud IPs (Colab) - handled gracefully
- Browser tests marked with `@pytest.mark.slow`
- IR/LLM unit tests use mocks (fast, no network)
- Calendar tests pass `include_ir=False` for speed

## Remaining Tasks

- `tasks/todo/TASK-016-configuration.md` - Configuration system (LLM provider settings, timeouts)

## Related Projects

- **vibe-trader** - Event backtesting uses this library for earnings dates
  - Spec: `/dev/vibe-trader/docs/specs/event-backtest.md`
