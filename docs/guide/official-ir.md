# Official IR Verification

The most accurate earnings datetime comes from company investor relations (IR) pages. This feature attempts to discover and parse official announcement times.

## How It Works

```python
df = cal.get_calendar("2025-02-14", verify_official=True)
```

For each company in the calendar:

1. **Check cache** - Skip if we already know this company's IR URL and policy
2. **Check if significant** - Skip if time >= 15:30 (after-hours, doesn't affect trading)
3. **Try pattern matching** - Look for common IR URL patterns
4. **LLM fallback** - Use local LLM to discover IR page
5. **Parse datetime** - Extract announcement time from IR page
6. **Cache result** - Save URL and `publishes_time` policy for future

## Trading Hours Optimization

Only companies announcing during trading hours (zaraba) are checked:

| Session | Time |
|---------|------|
| Morning | 9:00 - 11:30 |
| Afternoon | 12:30 - 15:30 |

If the scraped time is after 15:30, official verification is skipped since the exact time doesn't affect trading decisions.

## Caching

Discovered IR paths are cached for future use:

```json
{
  "7203": {
    "ir_url": "https://global.toyota/jp/ir/calendar/",
    "publishes_time": true,
    "last_checked": "2025-01-15"
  },
  "6758": {
    "ir_url": "https://www.sony.com/ja/SonyInfo/IR/",
    "publishes_time": false,
    "last_checked": "2025-01-15"
  }
}
```

- `publishes_time: true` - Company publishes exact time, check each season
- `publishes_time: false` - Company only publishes date, skip time verification

## Eager Mode

Occasionally refresh the cache to catch policy changes:

```python
# Normal mode - respects cache
df = cal.get_calendar("2025-02-14", verify_official=True)

# Eager mode - ignores cache, re-checks everything
df = cal.get_calendar("2025-02-14", verify_official=True, eager=True)
```

Run eager mode quarterly or when you suspect policies have changed.

## Manual Path Input

Users can manually add IR URLs to the cache:

1. Open `~/.pykabu_calendar/ir_cache.json`
2. Add entry for the company
3. Next run will use the cached path

This is useful when automatic discovery fails but you know the URL.

## Timeout Behavior

- Each company has a 30-second timeout
- If discovery fails, returns `None` and moves on
- Never blocks the entire calendar for one stubborn company

## LLM Configuration

When pattern matching fails, a local LLM helps discover IR pages:

```python
cal.configure(llm_provider="ollama", llm_model="llama3.2")
```

The LLM:

1. Analyzes the company homepage
2. Looks for IR-related links
3. Navigates to find earnings calendar
4. Learns from accumulated successful patterns
