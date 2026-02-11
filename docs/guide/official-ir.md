# Official IR Verification

The most accurate earnings datetime comes from company investor relations (IR) pages. pykabu-calendar discovers and parses official announcement times automatically.

## How It Works

For each company in the calendar:

1. **Check cache** - Skip if we already have a recent IR result for this company
2. **Get company website** - Look up via pykabutan
3. **Try pattern matching** - Check common IR URL patterns (`/ir/`, `/investor/`, `/ir/calendar/`)
4. **Search homepage** - Parse the company homepage for IR links (rule-based)
5. **LLM fallback** - Use Gemini to find the IR page link in the HTML
6. **Parse datetime** - Extract announcement time from the IR page (rule-based, then LLM fallback)
7. **Cache result** - Save URL and parsed datetime for future reuse

## Usage

IR discovery is enabled by default:

```python
import pykabu_calendar as cal

# IR is included by default
df = cal.get_calendar("2026-02-10")

# Disable IR for faster results
df = cal.get_calendar("2026-02-10", include_ir=False)

# Force re-discovery (bypass cache)
df = cal.get_calendar("2026-02-10", ir_eager=True)
```

## Direct API

You can also use the IR discovery and parsing functions directly:

```python
from pykabu_calendar import discover_ir_page, parse_earnings_datetime

# Discover IR page for Toyota
page_info = discover_ir_page("7203")
if page_info:
    print(f"IR page: {page_info.url}")
    print(f"Type: {page_info.page_type.value}")
    print(f"Found via: {page_info.discovered_via}")

    # Parse earnings datetime from the page
    earnings = parse_earnings_datetime(page_info.url, code="7203")
    if earnings:
        print(f"Earnings: {earnings.datetime}")
        print(f"Confidence: {earnings.confidence.value}")
```

## Cache

Discovered IR pages are cached at `~/.pykabu_calendar/ir_cache.json` to avoid repeated lookups. Cache TTL is configurable:

```python
cal.configure(cache_ttl_days=7)  # Cache for 7 days (default: 30)
```
