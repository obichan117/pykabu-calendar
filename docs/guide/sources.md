# Data Sources

pykabu-calendar aggregates earnings calendar data from multiple sources, each with different characteristics.

## Available Sources

| Source | Browser Required | Speed | Notes |
|--------|-----------------|-------|-------|
| `sbi` | Yes (Playwright) | Slower | Most comprehensive, default |
| `matsui` | No | Fast | Lightweight, default |
| `tradersweb` | No | Fast | Lightweight, default |

## SBI Securities

The SBI calendar is the most comprehensive public source for Japanese earnings dates.

**URL**: `https://www.sbisec.co.jp/...`

**Data provided**:

- Announcement date and time
- Company code and name

**Requires**: Playwright browser automation

```bash
pip install playwright
playwright install chromium
```

```python
# SBI is included by default
df = cal.get_calendar("2026-02-10")

# Or use SBI only
df = cal.get_calendar("2026-02-10", sources=["sbi"])
```

## Matsui Securities

Lightweight source that doesn't require browser automation.

**URL**: `https://finance.matsui.co.jp/...`

**Data provided**:

- Announcement date and time
- Company code and name

```python
# Used by default
df = cal.get_calendar("2026-02-10")

# Or directly
df = cal.get_matsui("2026-02-10")
```

## Tradersweb

Independent source that can catch discrepancies with Matsui.

**URL**: `https://www.traders.co.jp/...`

**Data provided**:

- Announcement date and time
- Company code and name

```python
# Used by default
df = cal.get_calendar("2026-02-10")

# Or directly
df = cal.get_tradersweb("2026-02-10")
```

## Historical Inference

Uses past announcement patterns from [pykabutan](https://pypi.org/project/pykabutan/) to predict timing.

**Logic**:

1. Fetch past N earnings announcement times
2. Detect patterns (e.g., "always 13:00", "always after close")
3. Assign confidence based on consistency

**Example patterns**:

- Company always announces at 13:00 → high confidence
- Company varies between 11:00-15:00 → low confidence
- Company always announces after 15:30 → not significant for trading

```python
# Enabled by default
df = cal.get_calendar("2026-02-10", infer_from_history=True)

# View past earnings times for a specific stock
past = cal.get_past_earnings("7203")  # Toyota
```

## Datetime Selection Priority

When multiple sources provide different times:

1. **Inferred + Source match** - When inferred time matches a source (high confidence)
2. **Inferred** - From historical patterns
3. **SBI** - Primary public source
4. **Matsui** - Lightweight source
5. **Tradersweb** - Lightweight source

The `candidate_datetimes` column contains all possible times, ordered by confidence.
