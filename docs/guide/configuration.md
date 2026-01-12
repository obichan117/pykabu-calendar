# Configuration

## Shared Configuration

The library uses centralized configuration in `pykabu_calendar/config.py`:

```python
# User-Agent for HTTP requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# Request timeout in seconds
TIMEOUT = 30

# HTTP headers used for all requests
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
}
```

## Source-Specific Configuration

Each data source has its own configuration in `sources/{source}/config.py`:

### Matsui

```python
# sources/matsui/config.py
URL = "https://finance.matsui.co.jp/find-by-schedule/index"
TABLE_SELECTOR = "table.m-table"
DATE_FORMAT = "%Y/%m/%d"

def build_url(date: str, page: int = 1) -> str:
    # Builds URL like: .../index?d=2026/2/10&kind=earnings&p=1
```

### Tradersweb

```python
# sources/tradersweb/config.py
URL = "https://www.traders.co.jp/stocks/earnings/calendar"

def build_url(date: str) -> str:
    # Builds URL like: .../calendar/2026/02/10
```

### SBI

```python
# sources/sbi/config.py
URL = "https://www.sbisec.co.jp/ETGate/..."

def build_url(date: str) -> str:
    # Builds URL for SBI calendar page
```

## Modifying URLs

If a data source changes their URL structure:

1. Open `src/pykabu_calendar/sources/{source}/config.py`
2. Update the `URL` constant and/or `build_url()` function
3. Update any CSS selectors if the page structure changed

## Default Sources

```python
import pykabu_calendar as cal

# Default: uses all sources (sbi, matsui, tradersweb)
# Note: SBI requires Playwright and may be slightly slower
df = cal.get_calendar("2026-02-10")

# Use only lightweight sources (no Playwright needed, faster)
df = cal.get_calendar("2026-02-10", sources=["matsui", "tradersweb"])

# Use specific sources only
df = cal.get_calendar("2026-02-10", sources=["matsui"])

# Disable historical inference (faster)
df = cal.get_calendar("2026-02-10", infer_from_history=False)
```

## Installing Playwright for SBI

SBI requires browser automation because the site uses JavaScript rendering:

```bash
pip install playwright
playwright install chromium
```

SBI is included by default. To skip it, use `sources=["matsui", "tradersweb"]`.
