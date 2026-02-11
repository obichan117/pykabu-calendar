# Quick Start

## Basic Usage

Get the earnings calendar for a specific date:

```python
import pykabu_calendar as cal

# Get calendar for February 10, 2026
df = cal.get_calendar("2026-02-10")

print(df[["code", "name", "datetime", "inferred_datetime"]])
```

Output:

```
   code             name            datetime   inferred_datetime
0  1414   ショーボンドホールディングス 2026-02-10 15:30:00 2026-02-10 15:30:00
1  1446           キャンディル 2026-02-10 15:30:00 2026-02-10 15:30:00
2  167A  リョーサン菱洋ホールディングス 2026-02-10 16:00:00 2026-02-10 16:00:00
...
```

## Selecting Sources

By default, all sources are used (SBI, Matsui, Tradersweb):

```python
# Use only specific sources
df = cal.get_calendar("2026-02-10", sources=["matsui", "tradersweb"])

# Use only SBI
df = cal.get_calendar("2026-02-10", sources=["sbi"])
```

## Without Historical Inference

For faster results, disable historical inference:

```python
# Faster, but less accurate
df = cal.get_calendar("2026-02-10", infer_from_history=False)
```

## IR Page Enrichment

For the most accurate times, enable company IR page discovery:

```python
# Include IR page data (slower, most accurate)
df = cal.get_calendar("2026-02-10", include_ir=True)

# Check IR-specific datetime
print(df[["code", "name", "datetime", "ir_datetime"]])
```

## Viewing Past Datetimes

Each row includes historical earnings announcement times:

```python
df = cal.get_calendar("2026-02-10")

# Check past earnings times for first company
row = df.iloc[0]
print(f"Company: {row['name']}")
print(f"Past announcements: {row['past_datetimes']}")
```

Output:

```
Company: ショーボンドホールディングス
Past announcements: [Timestamp('2025-11-10 15:30:00'), Timestamp('2025-08-12 15:30:00'), ...]
```

## Candidate Datetimes

The `candidate_datetimes` column shows all possible times, ordered by confidence:

```python
df = cal.get_calendar("2026-02-10")

# When inferred matches source data, it's listed first (high confidence)
print(df[["code", "name", "candidate_datetimes"]].head())
```

## Export

```python
df = cal.get_calendar("2026-02-10")

# CSV (Excel/Google Sheets compatible)
cal.export_to_csv(df, "earnings_2026-02-10.csv")

# Parquet (requires pyarrow)
cal.export_to_parquet(df, "earnings.parquet")

# SQLite
cal.export_to_sqlite(df, "earnings.db")

# Load back from SQLite
df = cal.load_from_sqlite("earnings.db", date="2026-02-10")
```

## Health Checks

Verify data sources are working:

```python
results = cal.check_sources()
for r in results:
    status = "OK" if r["ok"] else "FAIL"
    print(f"  {r['name']}: {status} ({r['rows']} rows)")
```

## Output Columns

| Column | Description |
|--------|-------------|
| `code` | Stock code (e.g., "7203") |
| `name` | Company name |
| `datetime` | Best guess announcement datetime |
| `candidate_datetimes` | List of candidate datetimes (most likely first) |
| `ir_datetime` | Datetime from company IR page |
| `sbi_datetime` | Datetime from SBI |
| `matsui_datetime` | Datetime from Matsui |
| `tradersweb_datetime` | Datetime from Tradersweb |
| `inferred_datetime` | Datetime inferred from history |
| `past_datetimes` | List of past earnings datetimes |

## Using Individual Sources

You can also use individual source classes directly:

```python
from pykabu_calendar.earnings.sources import (
    MatsuiEarningsSource, TraderswebEarningsSource, SBIEarningsSource,
)

matsui = MatsuiEarningsSource()
df = matsui.fetch("2026-02-10")
```
