# pykabu-calendar

Japanese earnings calendar aggregator.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/obichan117/pykabu-calendar/blob/main/examples/quickstart.ipynb)

## Overview

**pykabu-calendar** aggregates earnings announcement data from multiple Japanese broker sites, company IR pages, and historical patterns to produce the most accurate earnings datetime calendar possible.

### Why accurate datetime matters

Some companies announce earnings during trading hours (zaraba: 9:00-11:30, 12:30-15:30). Knowing the exact announcement time allows traders to:

- Position before announcements
- React quickly to results
- Avoid unexpected volatility

### Data source hierarchy

1. **Company IR page** - Official IR page with exact announcement time (highest accuracy)
2. **Historical patterns** - Inferred from past announcement times via pykabutan
3. **SBI Securities** - JSONP API calendar
4. **Matsui/Tradersweb** - Lightweight HTML sources

## Quick Example

```python
import pykabu_calendar as cal

# Get earnings calendar (uses all sources by default)
df = cal.get_calendar("2026-02-10")

# Use specific sources only
df = cal.get_calendar("2026-02-10", sources=["matsui", "tradersweb"])

# Include company IR pages for exact times
df = cal.get_calendar("2026-02-10", include_ir=True)

# Export to CSV for Google Sheets
cal.export_to_csv(df, "earnings.csv")

# Export to Parquet or SQLite
cal.export_to_parquet(df, "earnings.parquet")
cal.export_to_sqlite(df, "earnings.db")

# Health check data sources
cal.check_sources()
```

## Output Columns

| Column | Description |
|--------|-------------|
| `code` | Stock code (e.g., "7203") |
| `name` | Company name |
| `datetime` | Best estimate datetime |
| `confidence` | Confidence level: "highest", "high", "medium", or "low" |
| `during_trading_hours` | Whether datetime falls within TSE trading hours |
| `candidate_datetimes` | List of candidate datetimes (most likely first) |
| `ir_datetime` | Datetime from company IR page |
| `sbi_datetime` | Datetime from SBI (if available) |
| `matsui_datetime` | Datetime from Matsui |
| `tradersweb_datetime` | Datetime from Tradersweb |
| `inferred_datetime` | Datetime inferred from history |
| `past_datetimes` | List of past earnings datetimes |

## Features

- Aggregates earnings calendars from SBI, Matsui, Tradersweb
- Discovers company IR pages and extracts exact announcement times
- Infers announcement time from historical patterns (via pykabutan)
- Parallel source fetching via `ThreadPoolExecutor`
- Source health checks via `check_sources()`
- YAML-based source configuration
- Exports to CSV, Parquet, and SQLite
- Extensible via `EarningsSource` ABC

## Installation

```bash
pip install pykabu-calendar
```

See [Installation](getting-started/installation.md) for more options.
