# pykabu-calendar

Japanese earnings calendar aggregator with official IR verification.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/obichan117/pykabu-calendar/blob/main/examples/quickstart.ipynb)

## Installation

```bash
pip install pykabu-calendar
```

## Quick Start

```python
import pykabu_calendar as cal

# Get earnings calendar for a specific date
df = cal.get_calendar("2026-02-10")

# Using lightweight sources only (no browser needed)
df = cal.get_calendar("2026-02-10", sources=["matsui", "tradersweb"])

# With historical inference
df = cal.get_calendar("2026-02-10", infer_from_history=True)

# Export to CSV
cal.export_to_csv(df, "earnings.csv")
```

## Features

- Aggregates earnings calendars from SBI, Matsui, Monex, Tradersweb
- Infers announcement time from historical patterns
- Optionally verifies against official company IR pages
- Caches IR discovery for fast subsequent runs
- Exports to CSV (Google Sheets compatible)

## Data Source Priority

1. **Official IR** - Most accurate (optional, slower)
2. **Historical patterns** - Inferred from past announcements
3. **SBI Securities** - Primary public source
4. **Supplementary sources** - Matsui, Monex, Tradersweb

## Documentation

Full documentation: https://obichan117.github.io/pykabu-calendar

## License

MIT
