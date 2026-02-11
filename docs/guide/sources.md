# Data Sources

pykabu-calendar aggregates earnings calendar data from multiple sources, each with different characteristics.

## Available Sources

| Source | Speed | Notes |
|--------|-------|-------|
| `sbi` | Fast | JSONP API, most comprehensive |
| `matsui` | Fast | HTML scraping, lightweight |
| `tradersweb` | Fast | HTML scraping, lightweight |

All sources are lightweight HTTP-based scrapers. No browser automation is required.

## SBI Securities

SBI uses a JSONP API endpoint for earnings calendar data.

**Data provided**:

- Announcement date and time
- Company code and name

```python
# SBI is included by default
df = cal.get_calendar("2026-02-10")

# Or use SBI only
df = cal.get_calendar("2026-02-10", sources=["sbi"])
```

## Matsui Securities

HTML-based scraper with pagination support.

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

Single-page HTML scraper.

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

## Company IR Pages

The library can discover and scrape company IR pages for exact announcement times.

```python
# Include IR page data (slower, more accurate)
df = cal.get_calendar("2026-02-10", include_ir=True)

# Force re-discovery (bypass cache)
df = cal.get_calendar("2026-02-10", include_ir=True, ir_eager=True)
```

## Datetime Selection Priority

When multiple sources provide different times:

1. **Company IR page** - Official source, most accurate
2. **Inferred + Source match** - When inferred time matches a source (high confidence)
3. **Inferred** - From historical patterns
4. **SBI** - Primary public source
5. **Matsui** - Lightweight source
6. **Tradersweb** - Lightweight source

The `candidate_datetimes` column contains all possible times, ordered by confidence.

## Health Checks

Verify that all sources are working:

```python
results = cal.check_sources()
for r in results:
    status = "OK" if r["ok"] else "FAIL"
    print(f"  {r['name']}: {status} ({r['rows']} rows)")
```

## Source Architecture

Each source is implemented as a subclass of `EarningsSource` ABC with an adjacent YAML config file:

```
earnings/sources/
├── sbi.py + sbi.yaml
├── matsui.py + matsui.yaml
└── tradersweb.py + tradersweb.yaml
```

The YAML config contains URLs, selectors, and health check parameters. The Python file contains the scraping logic.

## Adding a Custom Source

1. Create `mysource.py` and `mysource.yaml` in `earnings/sources/`
2. Subclass `EarningsSource`:

```python
from pykabu_calendar.earnings.base import EarningsSource, load_config

class MyEarningsSource(EarningsSource):
    def __init__(self):
        self._config = load_config(__file__)

    @property
    def name(self) -> str:
        return "mysource"

    def _fetch(self, date: str) -> pd.DataFrame:
        cfg = self._config
        # Your scraping logic using cfg values
        return pd.DataFrame({
            "code": ["7203"],
            "name": ["Toyota"],
            "datetime": ["2026-02-10 15:00"],
        })
```

3. Create `mysource.yaml`:

```yaml
url: "https://example.com/api/earnings"
health_check:
  test_date: "2026-02-10"
  min_rows: 1
```

4. Register in `earnings/sources/__init__.py` and `earnings/__init__.py`
