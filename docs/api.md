# API Reference

## Main Functions

### get_calendar

```python
def get_calendar(
    date: str,
    sources: list[str] | None = None,
    infer_from_history: bool = True,
) -> pd.DataFrame:
    """
    Get aggregated earnings calendar for a target date.

    Args:
        date: Date in YYYY-MM-DD format
        sources: List of sources to use. Default: all sources (sbi, matsui, tradersweb).
                 Note: SBI requires Playwright and may be slower than other sources.
        infer_from_history: Whether to infer time from historical patterns

    Returns:
        DataFrame with earnings calendar data
    """
```

### export_to_csv

```python
def export_to_csv(df: pd.DataFrame, path: str) -> None:
    """
    Export calendar to CSV with proper encoding for Excel/Google Sheets.

    Args:
        df: Calendar DataFrame
        path: Output file path
    """
```

## Individual Scrapers

### get_matsui

```python
def get_matsui(date: str) -> pd.DataFrame:
    """
    Get earnings calendar from Matsui Securities.

    Args:
        date: Target date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: [code, name, datetime]
    """
```

### get_tradersweb

```python
def get_tradersweb(date: str) -> pd.DataFrame:
    """
    Get earnings calendar from Tradersweb.

    Args:
        date: Target date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: [code, name, datetime]
    """
```

### get_sbi

```python
def get_sbi(date: str) -> pd.DataFrame:
    """
    Get earnings calendar from SBI Securities.

    Requires Playwright: pip install playwright && playwright install chromium

    Args:
        date: Target date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: [code, name, datetime]
    """
```

## Inference Functions

### get_past_earnings

```python
def get_past_earnings(code: str, n_recent: int = 8) -> list[pd.Timestamp]:
    """
    Get past earnings announcement datetimes for a stock.

    Uses pykabutan to fetch historical earnings data from kabutan.jp.

    Args:
        code: Stock code (e.g., "7203")
        n_recent: Number of recent announcements to fetch

    Returns:
        List of past announcement timestamps
    """
```

### infer_datetime

```python
def infer_datetime(
    code: str,
    target_date: str,
    n_recent: int = 8,
) -> tuple[pd.Timestamp | None, str, list[pd.Timestamp]]:
    """
    Infer earnings announcement datetime from historical patterns.

    Args:
        code: Stock code (e.g., "7203")
        target_date: Target date in YYYY-MM-DD format
        n_recent: Number of recent announcements to consider

    Returns:
        Tuple of (inferred_datetime, confidence, past_datetimes)
        - inferred_datetime: Predicted announcement time (or None)
        - confidence: "high", "medium", or "low"
        - past_datetimes: List of past announcement times used
    """
```

### is_during_trading_hours

```python
def is_during_trading_hours(dt: pd.Timestamp) -> bool:
    """
    Check if a datetime is during Tokyo Stock Exchange trading hours.

    Trading hours: 9:00-11:30, 12:30-15:00 JST

    Args:
        dt: Datetime to check

    Returns:
        True if during trading hours
    """
```

## Output Columns

| Column | Type | Description |
|--------|------|-------------|
| `code` | str | Stock code (e.g., "7203") |
| `name` | str | Company name in Japanese |
| `datetime` | datetime | Best estimate announcement datetime |
| `candidate_datetimes` | list | List of candidate datetimes (most likely first) |
| `sbi_datetime` | datetime | Datetime from SBI (if available) |
| `matsui_datetime` | datetime | Datetime from Matsui |
| `tradersweb_datetime` | datetime | Datetime from Tradersweb |
| `inferred_datetime` | datetime | Datetime inferred from history |
| `past_datetimes` | list | List of past earnings datetimes |

## Datetime Selection Priority

1. **Inferred + Source match** - When inferred time matches a source (high confidence)
2. **Inferred** - From historical patterns
3. **SBI** - Primary public source (requires Playwright)
4. **Matsui** - Lightweight source
5. **Tradersweb** - Lightweight source
