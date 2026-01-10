# API Reference

## Main Functions

### get_calendar

```python
def get_calendar(
    target_date: str,
    sources: list[str] = ["sbi", "matsui", "tradersweb"],
    infer_from_history: bool = True,
    verify_official: bool = False,
    eager: bool = False,
) -> pd.DataFrame:
    """
    Get earnings calendar for a specific date.

    Args:
        target_date: Date string in "YYYY-MM-DD" format
        sources: List of calendar sources to scrape
        infer_from_history: Whether to infer time from historical patterns
        verify_official: Whether to check company IR pages
        eager: If True, ignore cache and re-check all IR pages

    Returns:
        DataFrame with earnings calendar data
    """
```

### get_calendars

```python
def get_calendars(
    year_month: str,
    start_day: int = 1,
    **kwargs,
) -> list[pd.DataFrame]:
    """
    Get earnings calendars for multiple days in a month.

    Args:
        year_month: Year and month in "YYYY-MM" format
        start_day: Day to start from (default: 1)
        **kwargs: Passed to get_calendar()

    Returns:
        List of DataFrames, one per trading day
    """
```

### configure

```python
def configure(
    llm_provider: str = "ollama",
    llm_model: str = "llama3.2",
    timeout: int = 30,
    parallel_workers: int = 5,
    cache_path: str = None,
) -> None:
    """
    Configure library settings.

    Args:
        llm_provider: LLM provider ("ollama", "anthropic", "openai")
        llm_model: Model name
        timeout: Seconds per company for IR discovery
        parallel_workers: Concurrent IR verification workers
        cache_path: Custom cache directory path
    """
```

## Output Columns

| Column | Type | Description |
|--------|------|-------------|
| `code` | str | Stock code (e.g., "7203") |
| `name` | str | Company name in Japanese |
| `datetime` | datetime | Best guess announcement datetime |
| `datetime_source` | str | Source of datetime ("sbi", "inferred", "official") |
| `date` | date | Announcement date |
| `time_sbi` | str | Time from SBI calendar |
| `time_matsui` | str | Time from Matsui calendar |
| `time_tradersweb` | str | Time from Tradersweb calendar |
| `time_inferred` | str | Time inferred from history |
| `time_official` | str | Time from company IR |
| `type` | str | Earnings type (Q1, Q2, Q3, 本決算) |
| `ir_url` | str | Cached IR page URL |
| `publishes_time` | bool | Whether company publishes exact time |
| `confidence` | str | Confidence level (high, medium, low) |

## Source Classes

### BaseCalendarScraper

```python
class BaseCalendarScraper(ABC):
    """Abstract base class for calendar scrapers."""

    @abstractmethod
    def get_calendar(self, target_date: str) -> pd.DataFrame:
        """Scrape calendar for target date."""
        pass
```

### SbiCalendarScraper

```python
class SbiCalendarScraper(BaseCalendarScraper):
    """SBI Securities earnings calendar scraper."""
    pass
```

### MatsuiCalendarScraper

```python
class MatsuiCalendarScraper(BaseCalendarScraper):
    """Matsui Securities earnings calendar scraper."""
    pass
```

## Exceptions

```python
class CalendarScraperError(Exception):
    """Base exception for scraper errors."""
    pass

class SourceUnavailableError(CalendarScraperError):
    """Raised when a calendar source is unavailable."""
    pass

class IRDiscoveryError(CalendarScraperError):
    """Raised when IR page discovery fails."""
    pass
```
