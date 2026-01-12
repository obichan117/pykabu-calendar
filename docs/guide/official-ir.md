# Official IR Verification (Planned)

!!! warning "Not Yet Implemented"
    This feature is planned for a future release. The documentation below describes the intended design.

The most accurate earnings datetime comes from company investor relations (IR) pages. This feature would attempt to discover and parse official announcement times.

## Planned Behavior

For each company in the calendar:

1. **Check cache** - Skip if we already know this company's IR URL and policy
2. **Check if significant** - Skip if time >= 15:30 (after-hours, doesn't affect trading)
3. **Try pattern matching** - Look for common IR URL patterns
4. **LLM fallback** - Use local LLM to discover IR page
5. **Parse datetime** - Extract announcement time from IR page
6. **Cache result** - Save URL and `publishes_time` policy for future

## Trading Hours Optimization

Only companies announcing during trading hours (zaraba) would be checked:

| Session | Time |
|---------|------|
| Morning | 9:00 - 11:30 |
| Afternoon | 12:30 - 15:00 |

If the scraped time is after 15:30, official verification would be skipped since the exact time doesn't affect trading decisions.

## Current Alternative

For now, use historical inference which provides reasonably accurate predictions based on past patterns:

```python
import pykabu_calendar as cal

# Historical inference is enabled by default
df = cal.get_calendar("2026-02-10")

# Check inferred datetime and past patterns
print(df[["code", "name", "datetime", "inferred_datetime", "past_datetimes"]])
```
