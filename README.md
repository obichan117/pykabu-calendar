# pykabu-calendar

Japanese earnings calendar aggregator.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/obichan117/pykabu-calendar/blob/main/examples/quickstart.ipynb)

## Installation

```bash
pip install pykabu-calendar
```

## Quick Start

```python
import pykabu_calendar as cal

# Get earnings calendar (uses all sources by default)
df = cal.get_calendar("2026-02-10")

# Use specific sources only
df = cal.get_calendar("2026-02-10", sources=["matsui", "tradersweb"])

# Without historical inference (faster)
df = cal.get_calendar("2026-02-10", infer_from_history=False)

# Export to CSV
cal.export_to_csv(df, "earnings.csv")

# Export to Parquet (requires pyarrow)
cal.export_to_parquet(df, "earnings.parquet")

# Export to SQLite
cal.export_to_sqlite(df, "earnings.db")

# Load back from SQLite
df = cal.load_from_sqlite("earnings.db", date="2026-02-10")

# Health check all data sources
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
| `sbi_datetime` | Datetime from SBI |
| `matsui_datetime` | Datetime from Matsui |
| `tradersweb_datetime` | Datetime from Tradersweb |
| `inferred_datetime` | Datetime inferred from history |
| `past_datetimes` | List of past earnings datetimes |

## Features

- Aggregates earnings calendars from SBI, Matsui, Tradersweb
- Discovers company IR pages and extracts exact announcement times
- Infers announcement time from historical patterns (via pykabutan)
- Parallel source fetching for faster results
- Source health checks via `check_sources()`
- YAML-based source configuration for easy maintenance
- Exports to CSV, Parquet, and SQLite
- EarningsSource ABC for adding custom sources

## Data Source Priority

1. **IR page** - Company's official IR page (most accurate)
2. **Inferred** - From historical patterns
3. **SBI** - SBI Securities (JSONP API)
4. **Matsui** - Matsui Securities
5. **Tradersweb** - Tradersweb

## Documentation

Full documentation: https://obichan117.github.io/pykabu-calendar

## License

MIT
