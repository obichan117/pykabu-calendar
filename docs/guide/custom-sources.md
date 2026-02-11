# Adding Custom Sources

pykabu-calendar provides an `EarningsSource` abstract base class that you can subclass to add your own data sources.

## Overview

Each source consists of:

1. A Python file with your scraping logic (subclass of `EarningsSource`)
2. A YAML config file with URLs, selectors, and health check parameters

## Step-by-Step

### 1. Create the YAML config

Create `mysource.yaml` alongside your Python file:

```yaml
url: "https://example.com/api/earnings"
headers:
  Accept: "application/json"
health_check:
  test_date: "2026-02-10"
  min_rows: 1
```

### 2. Create the source class

Create `mysource.py`:

```python
import pandas as pd
from pykabu_calendar.earnings.base import EarningsSource, load_config

class MyEarningsSource(EarningsSource):
    def __init__(self):
        self._config = load_config(__file__)

    @property
    def name(self) -> str:
        return "mysource"

    def _fetch(self, date: str) -> pd.DataFrame:
        cfg = self._config
        # Your scraping/API logic here
        # Must return DataFrame with at least 'code' and 'datetime' columns
        return pd.DataFrame({
            "code": ["7203", "6758"],
            "name": ["Toyota", "Sony"],
            "datetime": [f"{date} 15:00", f"{date} 16:00"],
        })

# Convenience function
_source = MyEarningsSource()

def get_mysource(date: str) -> pd.DataFrame:
    return _source.fetch(date)
```

### 3. Validation

The `EarningsSource.fetch()` method automatically validates your data:

- **code**: Coerced to string, validated against `^[0-9A-Za-z]{4}$`
- **datetime**: Coerced via `pd.to_datetime(errors="coerce")`
- Invalid rows are dropped with a warning

### 4. Health check

The `check()` method uses your YAML config's `health_check` section:

```python
source = MyEarningsSource()
result = source.check()
# {'name': 'mysource', 'ok': True, 'rows': 42, 'error': None}
```

## Built-in Sources

The library ships with three sources:

| Class | Name | Config |
|-------|------|--------|
| `SBIEarningsSource` | `sbi` | `sbi.yaml` |
| `MatsuiEarningsSource` | `matsui` | `matsui.yaml` |
| `TraderswebEarningsSource` | `tradersweb` | `tradersweb.yaml` |

Source files are located at `src/pykabu_calendar/earnings/sources/`.
