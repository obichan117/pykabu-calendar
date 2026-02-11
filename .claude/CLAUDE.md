# pykabu-calendar

Japanese earnings calendar aggregator. Scrapes multiple broker sites, company IR pages, and infers announcement times from historical patterns.

## Quick Start

```bash
# Setup
uv sync

# Run tests
uv run pytest

# Run tests (skip slow tests)
uv run pytest -k "not slow"

# Serve docs locally
uv run mkdocs serve

# Deploy docs
uv run mkdocs gh-deploy --force

# Publish to PyPI
uv build && uv run twine upload dist/* -u __token__ -p $PYPI_TOKEN
```

## Architecture (v0.8.0)

```
src/pykabu_calendar/
├── cli.py                 # Click CLI: pykabu calendar|check|lookup|config
├── config.py              # Settings dataclass, configure(), get_settings()
├── config.yaml            # Default values loaded at import time
├── core/
│   ├── fetch.py           # Generic fetch (requests, thread-safe sessions)
│   ├── parse.py           # Generic parse (tables, regex, datetime)
│   ├── parallel.py        # ThreadPoolExecutor-based parallel runner
│   └── io.py              # Export: CSV, Parquet, SQLite; Import: SQLite
├── earnings/              # Event-type module
│   ├── base.py            # EarningsSource ABC + YAML config loader
│   ├── calendar.py        # Aggregator: get_calendar(), check_sources()
│   ├── inference.py       # Historical inference via pykabutan
│   ├── sources/
│   │   ├── sbi.py + sbi.yaml         # SBI Securities (JSONP API)
│   │   ├── matsui.py + matsui.yaml   # Matsui Securities
│   │   └── tradersweb.py + tradersweb.yaml  # Tradersweb
│   └── ir/                # Company IR page discovery
│       ├── discovery.py   # Find IR pages from company website
│       ├── parser.py      # Rule-based datetime extraction + LLM fallback
│       ├── patterns.py    # Common IR URL/HTML patterns
│       └── cache.py       # Cache discovered patterns (JSON)
├── llm/                   # LLM-assisted parsing
│   ├── base.py            # Abstract LLM interface + get_default_client()
│   └── gemini.py          # Google Gemini free tier client
└── __init__.py            # Public API re-exports
```

## Data Source Priority

```
1. ir_datetime      # Company IR page (most accurate, exact times)
2. inferred         # Historical patterns via pykabutan
3. sbi              # SBI Securities calendar (JSONP API, no browser)
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
| `cli.py` | Click CLI entry point (`pykabu calendar\|check\|lookup\|config`) |
| `config.py` | `Settings` dataclass, `configure()`, `get_settings()`, `on_configure()` |
| `config.yaml` | Default values for all settings (timeout, max_workers, LLM params, cache) |
| `earnings/calendar.py` | Main aggregator, parallel fetching, IR integration, candidate ranking |
| `earnings/base.py` | `EarningsSource` ABC, `load_config()`, validation, health check |
| `earnings/inference.py` | Uses pykabutan for historical earnings patterns |
| `earnings/sources/*.yaml` | URLs, selectors, health check config — update here when sites change |
| `earnings/ir/discovery.py` | Find company IR pages (pattern → homepage → LLM) |
| `earnings/ir/parser.py` | Parse earnings datetime from IR pages (rule-based → LLM) |
| `earnings/ir/cache.py` | Thread-safe JSON cache at `~/.pykabu_calendar/ir_cache.json` |
| `core/fetch.py` | Thread-safe `get_session()` (version-based reset), `fetch()`, `fetch_safe()` |
| `core/parallel.py` | `run_parallel()` — ThreadPoolExecutor wrapper |
| `core/io.py` | `export_to_csv()`, `export_to_parquet()`, `export_to_sqlite()`, `load_from_sqlite()` |
| `core/parse.py` | `parse_table()`, `extract_regex()`, `to_datetime()`, `combine_datetime()` |
| `llm/base.py` | Abstract `LLMClient` + `get_default_client()` singleton |
| `llm/gemini.py` | `GeminiClient` with rate limiting |
| `docs/dev/sbi-api.md` | SBI JSONP API documentation (moved from sources/) |

## Configuration

```python
import pykabu_calendar as cal

# Override settings at runtime
cal.configure(llm_model="gemini-2.0-flash-lite", cache_ttl_days=7)

# Control parallelism
cal.configure(max_workers=8)

# Inspect current settings
cal.get_settings()

# Reset to defaults
cal.configure()

# Health check all sources
cal.check_sources()
```

## Output Schema

```python
df = cal.get_calendar("2026-02-10")
# Columns: code, name, datetime, confidence, during_trading_hours,
#          candidate_datetimes, ir_datetime, sbi_datetime, matsui_datetime,
#          tradersweb_datetime, inferred_datetime, past_datetimes
#
# confidence: "highest" (IR), "high" (inferred+scraper agree or 2+ scrapers agree),
#             "medium" (multiple sources, no agreement), "low" (single source)
# during_trading_hours: bool — True if datetime falls within TSE trading hours
#   (morning: 9:00-11:30, afternoon: 12:30-15:30)

# Disable IR for speed
df = cal.get_calendar("2026-02-10", include_ir=False)

# Force IR re-discovery (bypass cache)
df = cal.get_calendar("2026-02-10", ir_eager=True)

# Export to different formats
cal.export_to_csv(df, "earnings.csv")
cal.export_to_parquet(df, "earnings.parquet")
cal.export_to_sqlite(df, "earnings.db")
```

## Testing Notes

- Tests use **dynamic dates** (finds future weekday with earnings, skips weekends)
- `conftest.py` has offline fallback — falls back to next weekday if Matsui is unreachable
- Tradersweb blocks cloud IPs (Colab) - handled gracefully
- SBI uses JSONP API (fast, no browser needed)
- `@pytest.mark.slow` reserved for network-dependent integration tests
- IR/LLM unit tests use mocks (fast, no network)
- `test_calendar_unit.py` — fast unit tests for `_merge_sources`, `_build_candidates`, `check_sources`, confidence scoring
- `test_calendar_integration.py` — slow integration tests with real network calls
- Calendar integration tests pass `include_ir=False` for speed
- Parquet tests skip if `pyarrow` not installed

## Thread Safety

- `IRCache` — instance-level `threading.Lock` protects `get()`, `set()`, `delete()`, `clear()`
- `get_cache()` — global singleton access protected by `_global_cache_lock`
- `core/fetch.py` — `_session_version` protected by `_version_lock`; per-thread sessions via `threading.local()`
- `core/io.py` — `load_from_sqlite` validates table names against `^[a-zA-Z_][a-zA-Z0-9_]*$`

## Related Projects

- **vibe-trader** - Event backtesting uses this library for earnings dates
  - Spec: `/dev/vibe-trader/docs/specs/event-backtest.md`
