# Data Sources

pykabu-calendar aggregates earnings calendar data from multiple sources, each with different characteristics.

## Source Hierarchy

| Priority | Source | Description | Reliability |
|----------|--------|-------------|-------------|
| 1 | Official IR | Company investor relations pages | Highest |
| 2 | Historical | Inferred from past patterns | High |
| 3 | SBI | SBI Securities calendar | Good (primary) |
| 4 | Matsui | Matsui Securities calendar | Good |
| 5 | Monex | Monex Securities calendar | Moderate |
| 6 | Tradersweb | Tradersweb calendar | Good |

## SBI Securities (Primary)

The SBI calendar is the most comprehensive public source for Japanese earnings dates.

**URL Pattern**: `https://www.sbisec.co.jp/...`

**Data provided**:

- Announcement date and time
- Company code and name
- Earnings type (Q1, Q2, Q3, Full year)
- Result, guidance, and consensus estimates
- Percent gap (guidance vs consensus)

**Limitations**:

- Time may be inaccurate or missing for some companies
- Updates may lag behind official announcements

## Matsui Securities

Supplementary source that often confirms SBI data.

**Data provided**:

- Announcement date and time
- Company code and name
- Earnings type

## Monex Securities

Smaller coverage, often a subset of SBI.

**Data provided**:

- Announcement date and time
- Company code and name
- Earnings type

## Tradersweb

Independent source that can catch discrepancies.

**Data provided**:

- Announcement date and time
- Company code and name
- Earnings type

## Historical Inference

Uses past announcement patterns from pykabutan to predict timing.

**Logic**:

1. Fetch past N earnings announcement times
2. Detect patterns (e.g., "always 13:00", "always after close")
3. Assign confidence based on consistency

**Example patterns**:

- Company always announces at 13:00 → high confidence
- Company varies between 11:00-15:00 → low confidence
- Company always announces after 15:30 → not significant for trading

## Merging Strategy

When sources disagree:

1. Official IR time (if verified) takes precedence
2. Historical inference (if consistent pattern exists)
3. First available: SBI → Matsui → Tradersweb

The `datetime_source` column indicates which source provided the final datetime.
