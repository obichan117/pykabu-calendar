# pykabu-calendar

Japanese earnings calendar aggregator with official IR verification.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/obichan117/pykabu-calendar/blob/main/examples/quickstart.ipynb)

## Overview

**pykabu-calendar** aggregates earnings announcement data from multiple Japanese broker sites and produces the most accurate earnings datetime calendar possible.

### Why accurate datetime matters

Some companies announce earnings during trading hours (zaraba: 9:00-11:30, 12:30-15:30). Knowing the exact announcement time allows traders to:

- Position before announcements
- React quickly to results
- Avoid unexpected volatility

### Data source hierarchy

1. **Official company IR** - Most accurate, but slow to fetch
2. **Historical patterns** - Inferred from past announcement times
3. **SBI Securities** - Primary public calendar source
4. **Supplementary sources** - Matsui, Monex, Tradersweb

## Quick Example

```python
import pykabu_calendar as cal

# Get earnings calendar for a specific date
df = cal.get_calendar("2026-02-10")

# Using lightweight sources only (no browser needed)
df = cal.get_calendar("2026-02-10", sources=["matsui", "tradersweb"])

# With historical inference (default: True)
df = cal.get_calendar("2026-02-10", infer_from_history=True)

# Export to CSV for Google Sheets
cal.export_to_csv(df, "earnings.csv")
```

## Features

- Scrapes earnings calendars from SBI, Matsui, Monex, Tradersweb
- Merges data with intelligent conflict resolution
- Infers announcement time from historical patterns
- Optionally verifies against official company IR pages
- Caches IR discovery results for fast subsequent runs
- Exports to CSV (Google Sheets compatible)

## Installation

```bash
pip install pykabu-calendar
```

See [Installation](getting-started/installation.md) for more options.
