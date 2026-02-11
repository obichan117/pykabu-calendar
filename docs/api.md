# API Reference

## Main Functions

### get_calendar

```python
def get_calendar(
    date: str,
    sources: list[str] | None = None,
    infer_from_history: bool = True,
    include_ir: bool = True,
    ir_eager: bool = False,
    llm_client: LLMClient | None = None,
) -> pd.DataFrame:
    """
    Get aggregated earnings calendar for a target date.

    Args:
        date: Date in YYYY-MM-DD format
        sources: List of sources to use. Default: all sources (sbi, matsui, tradersweb).
        infer_from_history: Whether to infer time from historical patterns
        include_ir: Whether to enrich with company IR page data (default True)
        ir_eager: Force IR re-discovery (bypass cache)
        llm_client: Optional LLM client for IR discovery/parsing

    Returns:
        DataFrame with earnings calendar data
    """
```

### check_sources

```python
def check_sources() -> list[dict]:
    """
    Health check all registered earnings sources.

    Each source uses its YAML config's health_check section
    (test_date and min_rows) to validate.

    Returns:
        List of dicts with keys: name, ok, rows, error
    """
```

### export_to_csv

```python
def export_to_csv(df: pd.DataFrame, path: str) -> None:
    """
    Export calendar to CSV with proper encoding for Excel/Google Sheets.

    List columns are serialized as semicolon-separated strings.
    Uses utf-8-sig encoding.

    Args:
        df: Calendar DataFrame
        path: Output file path
    """
```

### export_to_parquet

```python
def export_to_parquet(df: pd.DataFrame, path: str) -> None:
    """
    Export calendar to Parquet format.

    Requires pyarrow or fastparquet.

    Args:
        df: Calendar DataFrame
        path: Output file path
    """
```

### export_to_sqlite

```python
def export_to_sqlite(
    df: pd.DataFrame,
    path: str,
    table: str = "earnings",
) -> None:
    """
    Export calendar to SQLite database.

    Args:
        df: Calendar DataFrame
        path: Database file path
        table: Table name (default: "earnings")
    """
```

### load_from_sqlite

```python
def load_from_sqlite(
    path: str,
    table: str = "earnings",
    date: str | None = None,
) -> pd.DataFrame:
    """
    Load calendar from SQLite database.

    Args:
        path: Database file path
        table: Table name (default: "earnings")
        date: Optional date filter (YYYY-MM-DD)

    Returns:
        Calendar DataFrame
    """
```

## IR Discovery

### discover_ir_page

```python
def discover_ir_page(
    code: str,
    llm_client: LLMClient | None = None,
    use_llm_fallback: bool = True,
    timeout: int | None = None,
) -> IRPageInfo | None:
    """
    Discover the IR page for a company.

    Flow:
    1. Get company website from pykabutan
    2. Try candidate URLs from common patterns
    3. If not found, fetch homepage and search for IR link
    4. If still not found and LLM enabled, use LLM to find link

    Args:
        code: Stock code (e.g., "7203")
        llm_client: Optional LLM client for fallback discovery
        use_llm_fallback: Whether to use LLM as fallback (default True)
        timeout: Request timeout in seconds

    Returns:
        IRPageInfo if found, None otherwise
    """
```

### parse_earnings_datetime

```python
def parse_earnings_datetime(
    url: str,
    code: str | None = None,
    llm_client: LLMClient | None = None,
    use_llm_fallback: bool = True,
    timeout: int | None = None,
) -> EarningsInfo | None:
    """
    Parse earnings announcement datetime from an IR page.

    Args:
        url: URL of the IR page
        code: Optional stock code to help locate relevant info
        llm_client: Optional LLM client for fallback parsing
        use_llm_fallback: Whether to use LLM as fallback
        timeout: Request timeout in seconds

    Returns:
        EarningsInfo if found, None otherwise
    """
```

## EarningsSource ABC

```python
class EarningsSource(ABC):
    """
    Abstract base class for earnings calendar sources.

    Subclass this to add a custom source.

    Properties:
        name: Short lowercase identifier (e.g., "sbi")

    Methods:
        fetch(date): Fetch and validate earnings data
        check(): Health check using YAML config
    """
```

### Adding a Custom Source

```python
from pykabu_calendar.earnings.base import EarningsSource, load_config

class MySource(EarningsSource):
    def __init__(self):
        self._config = load_config(__file__)

    @property
    def name(self) -> str:
        return "mysource"

    def _fetch(self, date: str) -> pd.DataFrame:
        # Your scraping logic here
        return pd.DataFrame({"code": [...], "name": [...], "datetime": [...]})
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
    date: str,
    past_datetimes: list[pd.Timestamp] | None = None,
) -> tuple[pd.Timestamp | None, str, list[pd.Timestamp]]:
    """
    Infer earnings announcement datetime from historical patterns.

    Args:
        code: Stock code (e.g., "7203")
        date: Target date in YYYY-MM-DD format
        past_datetimes: Optional pre-fetched past datetimes

    Returns:
        Tuple of (inferred_datetime, confidence, past_datetimes)
        - inferred_datetime: Predicted announcement time (or None)
        - confidence: "high", "medium", "low", or "none"
        - past_datetimes: List of past announcement times used
    """
```

### is_during_trading_hours

```python
def is_during_trading_hours(dt: pd.Timestamp) -> bool:
    """
    Check if a datetime is during Tokyo Stock Exchange trading hours.

    Trading hours: 9:00-11:30, 12:30-15:30 JST

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
| `confidence` | str | Confidence level: "highest", "high", "medium", or "low" |
| `during_trading_hours` | bool | Whether datetime falls within TSE trading hours (9:00-11:30, 12:30-15:30) |
| `candidate_datetimes` | list | List of candidate datetimes (most likely first) |
| `ir_datetime` | datetime | Datetime from company IR page |
| `sbi_datetime` | datetime | Datetime from SBI (if available) |
| `matsui_datetime` | datetime | Datetime from Matsui |
| `tradersweb_datetime` | datetime | Datetime from Tradersweb |
| `inferred_datetime` | datetime | Datetime inferred from history |
| `past_datetimes` | list | List of past earnings datetimes |

## Datetime Selection Priority

1. **Company IR page** - Official IR page (most accurate)
2. **Inferred + Source match** - When inferred time matches a source (high confidence)
3. **Inferred** - From historical patterns
4. **SBI** - JSONP API source
5. **Matsui** - Lightweight source
6. **Tradersweb** - Lightweight source
