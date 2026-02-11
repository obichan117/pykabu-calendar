# Configuration

## Runtime Configuration

Configure the library at runtime using `configure()`:

```python
import pykabu_calendar as cal

# Override settings
cal.configure(
    timeout=10,                       # HTTP timeout in seconds
    llm_model="gemini-2.0-flash-lite", # LLM model for IR parsing
    cache_ttl_days=7,                  # IR cache TTL
)

# Inspect current settings
settings = cal.get_settings()
print(settings.timeout)  # 10

# Reset to defaults
cal.configure()
```

## Settings Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `timeout` | `30` | HTTP request timeout (seconds) |
| `user_agent` | Chrome 131 | User-Agent header |
| `llm_model` | `"gemini-2.0-flash"` | LLM model for IR parsing |
| `llm_timeout` | `60.0` | LLM request timeout (seconds) |
| `llm_provider` | `"gemini"` | LLM provider |
| `cache_dir` | `"~/.pykabu_calendar"` | Cache directory |
| `cache_ttl_days` | `30` | Cache TTL in days |

## Source-Specific Configuration (YAML)

Each data source has an adjacent YAML config file:

### Matsui (`earnings/sources/matsui.yaml`)

```yaml
url: "https://finance.matsui.co.jp/find-by-schedule/index"
table_selector: "table.m-table"
date_format: "%Y/%m/%d"
per_page: 100
health_check:
  test_date: "2026-02-10"
  min_rows: 10
```

### Tradersweb (`earnings/sources/tradersweb.yaml`)

```yaml
url: "https://www.traders.co.jp/stocks/earnings/calendar"
table_selector: "table"
date_format: "%Y/%m/%d"
health_check:
  test_date: "2026-02-10"
  min_rows: 10
```

### SBI (`earnings/sources/sbi.yaml`)

```yaml
page_url: "https://www.sbisec.co.jp/ETGate/..."
api_endpoint: "https://www.sbisec.co.jp/ETGate/..."
hash_pattern: "hashKey=(\\w+)"
health_check:
  test_date: "2026-02-10"
  min_rows: 10
```

## Modifying Source URLs

If a data source changes their URL structure:

1. Open `src/pykabu_calendar/earnings/sources/{source}.yaml`
2. Update the URL and any selectors
3. Run health check to verify: `cal.check_sources()`

## Health Checks

Verify all sources are operational:

```python
results = cal.check_sources()
for r in results:
    status = "OK" if r["ok"] else "FAIL"
    print(f"  {r['name']}: {status} ({r['rows']} rows)")
    if r["error"]:
        print(f"    Error: {r['error']}")
```

## Default Sources

```python
import pykabu_calendar as cal

# Default: uses all sources (sbi, matsui, tradersweb)
df = cal.get_calendar("2026-02-10")

# Use only specific sources
df = cal.get_calendar("2026-02-10", sources=["matsui", "tradersweb"])

# Include IR page enrichment
df = cal.get_calendar("2026-02-10", include_ir=True)

# Disable historical inference (faster)
df = cal.get_calendar("2026-02-10", infer_from_history=False)
```
