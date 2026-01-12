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

By default, all sources are used (SBI, Matsui, Tradersweb). For faster results without browser automation:

```python
# Use only lightweight sources (no Playwright needed)
df = cal.get_calendar("2026-02-10", sources=["matsui", "tradersweb"])

# Use only SBI (requires Playwright)
df = cal.get_calendar("2026-02-10", sources=["sbi"])

# Check SBI-specific datetime
print(df[["code", "name", "datetime", "sbi_datetime"]])
```

Note: SBI requires Playwright and may be slightly slower than other sources.

## Without Historical Inference

For faster results, disable historical inference:

```python
# Faster, but less accurate
df = cal.get_calendar("2026-02-10", infer_from_history=False)
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

## Export to CSV

```python
df = cal.get_calendar("2026-02-10")

# Use the built-in export function (handles list columns)
cal.export_to_csv(df, "earnings_2026-02-10.csv")

# Or use pandas directly
df.to_csv("earnings.csv", index=False, encoding="utf-8-sig")
```

The `utf-8-sig` encoding ensures Excel and Google Sheets handle Japanese characters correctly.

## Output Columns

| Column | Description |
|--------|-------------|
| `code` | Stock code (e.g., "7203") |
| `name` | Company name |
| `datetime` | Best guess announcement datetime |
| `candidate_datetimes` | List of candidate datetimes (most likely first) |
| `sbi_datetime` | Datetime from SBI |
| `matsui_datetime` | Datetime from Matsui |
| `tradersweb_datetime` | Datetime from Tradersweb |
| `inferred_datetime` | Datetime inferred from history |
| `past_datetimes` | List of past earnings datetimes |

## Using Individual Scrapers

You can also use individual scrapers directly:

```python
import pykabu_calendar as cal

# Matsui (lightweight)
df_matsui = cal.get_matsui("2026-02-10")

# Tradersweb (lightweight)
df_tradersweb = cal.get_tradersweb("2026-02-10")

# SBI (requires Playwright)
df_sbi = cal.get_sbi("2026-02-10")
```
