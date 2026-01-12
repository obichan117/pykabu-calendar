# pykabu-calendar

Japanese earnings calendar aggregator. Scrapes multiple broker sites and infers announcement times from historical patterns.

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

Follows the [Scraping Library Pattern](~/.claude/patterns/scraping.md):

```
src/pykabu_calendar/
├── config.py              # Shared: USER_AGENT, TIMEOUT, HEADERS
├── core/
│   ├── fetch.py           # Generic fetch (requests, browser)
│   └── parse.py           # Generic parse (tables, regex, datetime)
├── sources/
│   ├── matsui/            # Matsui Securities
│   │   ├── config.py      # URL, selectors, date format
│   │   └── scraper.py     # get_matsui(date)
│   ├── tradersweb/        # Tradersweb
│   │   ├── config.py
│   │   └── scraper.py     # get_tradersweb(date)
│   └── sbi/               # SBI Securities (requires Playwright)
│       ├── config.py
│       └── scraper.py     # get_sbi(date)
├── calendar.py            # Aggregator: get_calendar(), export_to_csv()
└── inference.py           # Historical inference: infer_datetime(), get_past_earnings()
```

## Key Files

| File | Purpose |
|------|---------|
| `calendar.py` | Main aggregator, merges sources, builds candidate datetimes |
| `inference.py` | Uses pykabutan for historical earnings patterns |
| `core/fetch.py` | `fetch()`, `fetch_browser()`, `fetch_browser_with_pagination()` |
| `core/parse.py` | `parse_table()`, `extract_regex()`, `to_datetime()`, `combine_datetime()` |
| `sources/*/config.py` | URLs, selectors - update here when sites change |

## Output Schema

```python
df = cal.get_calendar("2026-02-10")
# Columns: code, name, datetime, candidate_datetimes,
#          sbi_datetime, matsui_datetime, tradersweb_datetime,
#          inferred_datetime, past_datetimes
```

## Testing Notes

- Tests use **dynamic dates** (finds future date with earnings)
- Tradersweb blocks cloud IPs (Colab) - handled gracefully
- Browser tests marked with `@pytest.mark.slow`
