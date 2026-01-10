# Quick Start

## Basic Usage

Get the earnings calendar for a specific date:

```python
import pykabu_calendar as cal

# Get calendar for February 10, 2026
df = cal.get_calendar("2026-02-10")

print(df[["code", "name", "datetime", "time_source"]])
```

Output:

```
   code             name            datetime time_source
0  5076  インフロニア・ホールディングス 2026-02-10 10:00:00         sbi
1  3405              クラレ 2026-02-10 11:00:00         sbi
2  7183           あんしん保証 2026-02-10 11:00:00         sbi
...
```

## Choosing Data Sources

```python
# Use only lightweight sources (fastest, no browser needed)
df = cal.get_calendar("2026-02-10", sources=["matsui", "tradersweb"])

# Use all available sources including SBI (requires Playwright)
df = cal.get_calendar("2026-02-10", sources=["sbi", "matsui", "tradersweb"])

# Disable historical inference (faster)
df = cal.get_calendar("2026-02-10", infer_from_history=False)
```

## With Historical Inference

Historical inference uses past announcement patterns to predict time:

```python
# Enable historical inference (default)
df = cal.get_calendar("2026-02-10", infer_from_history=True)

# Check inference confidence
print(df[["code", "name", "time", "time_source", "inference_confidence"]])
```

!!! tip
    Inference works best for companies with consistent announcement patterns.
    Confidence levels: `high` (always same time), `medium` (mostly same), `low` (varies).

## Export to CSV

```python
df = cal.get_calendar("2026-02-10")

# Use the built-in export function
cal.export_to_csv(df, "earnings_2026-02-10.csv")

# Or use pandas directly (with BOM for Excel/Google Sheets)
df.to_csv("earnings.csv", index=False, encoding="utf-8-sig")
```

The `utf-8-sig` encoding ensures Excel and Google Sheets handle Japanese characters correctly.

## Configuration

```python
# Configure settings
cal.configure(
    timeout=60,          # Request timeout in seconds
    llm_model="llama3.2" # For future IR discovery
)
```

## Output Columns

| Column | Description |
|--------|-------------|
| `code` | Stock code (e.g., "7203") |
| `name` | Company name |
| `datetime` | Best guess announcement datetime |
| `date` | Announcement date |
| `time` | Announcement time |
| `time_source` | Source of time (sbi, matsui, inferred, etc.) |
| `type` | Earnings type (3Q, 本決算, etc.) |
| `time_sbi` | Time from SBI |
| `time_matsui` | Time from Matsui |
| `time_tradersweb` | Time from Tradersweb |
| `time_inferred` | Time inferred from history |
| `inference_confidence` | Inference confidence level |
