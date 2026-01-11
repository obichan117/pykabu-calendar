# pykabu-calendar

Japanese earnings calendar aggregator.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/obichan117/pykabu-calendar/blob/main/examples/quickstart.ipynb)

## Installation

```bash
pip install pykabu-calendar
```

For SBI scraping (requires browser):
```bash
pip install pykabu-calendar
pip install playwright && playwright install chromium
```

## Quick Start

```python
import pykabu_calendar as cal

# Get earnings calendar for a specific date
df = cal.get_calendar("2026-02-10")

# Include SBI (requires Playwright)
df = cal.get_calendar("2026-02-10", include_sbi=True)

# Without historical inference (faster)
df = cal.get_calendar("2026-02-10", infer_from_history=False)

# Export to CSV
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

## Data Source Priority

1. **Inferred + Source match** - When inferred time matches a source
2. **Inferred** - From historical patterns
3. **SBI** - Primary public source (requires Playwright)
4. **Matsui/Tradersweb** - Lightweight sources (default)

## Documentation

Full documentation: https://obichan117.github.io/pykabu-calendar

## License

MIT
