# pykabu-calendar

Japanese earnings calendar aggregator.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/obichan117/pykabu-calendar/blob/main/examples/quickstart.ipynb)

## Overview

**pykabu-calendar** aggregates earnings announcement data from multiple Japanese broker sites and produces the most accurate earnings datetime calendar possible.

### Why accurate datetime matters

Some companies announce earnings during trading hours (zaraba: 9:00-11:30, 12:30-15:30). Knowing the exact announcement time allows traders to:

- Position before announcements
- React quickly to results
- Avoid unexpected volatility

### Data source hierarchy

1. **Inferred + Source match** - When historical pattern matches a source (high confidence)
2. **Historical patterns** - Inferred from past announcement times via pykabutan
3. **SBI Securities** - Primary public source (requires Playwright)
4. **Matsui/Tradersweb** - Lightweight sources (default)

## Quick Example

```python
import pykabu_calendar as cal

# Get earnings calendar for a specific date
df = cal.get_calendar("2026-02-10")

# Include SBI (requires Playwright)
df = cal.get_calendar("2026-02-10", include_sbi=True)

# Without historical inference (faster)
df = cal.get_calendar("2026-02-10", infer_from_history=False)

# Export to CSV for Google Sheets
cal.export_to_csv(df, "earnings.csv")
```

## Output Columns

| Column | Description |
|--------|-------------|
| `code` | Stock code (e.g., "7203") |
| `name` | Company name |
| `datetime` | Best estimate datetime |
| `candidate_datetimes` | List of candidate datetimes (most likely first) |
| `sbi_datetime` | Datetime from SBI (if available) |
| `matsui_datetime` | Datetime from Matsui |
| `tradersweb_datetime` | Datetime from Tradersweb |
| `inferred_datetime` | Datetime inferred from history |
| `past_datetimes` | List of past earnings datetimes |

## Features

- Aggregates earnings calendars from SBI, Matsui, Tradersweb
- Infers announcement time from historical patterns (via pykabutan)
- Centralized URL configuration for easy maintenance
- Modern User-Agent for reliable scraping
- Exports to CSV (Google Sheets compatible)

## Installation

```bash
pip install pykabu-calendar
```

For SBI scraping:
```bash
pip install playwright && playwright install chromium
```

See [Installation](getting-started/installation.md) for more options.
