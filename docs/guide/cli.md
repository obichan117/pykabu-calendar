# CLI

pykabu-calendar includes a command-line interface for quick terminal usage.

## Installation

The CLI is included with the base install:

```bash
pip install pykabu-calendar
```

Or run without installing via `uvx`:

```bash
uvx pykabu-calendar calendar 2026-02-10
```

## Commands

### `calendar` — Get earnings calendar

```bash
# Basic usage
pykabu-calendar calendar 2026-02-10

# Without IR discovery (faster)
pykabu-calendar calendar 2026-02-10 --no-ir

# Without historical inference
pykabu-calendar calendar 2026-02-10 --no-infer

# Force IR re-discovery (bypass cache)
pykabu-calendar calendar 2026-02-10 --ir-eager

# Use specific sources only
pykabu-calendar calendar 2026-02-10 --sources sbi,matsui

# Output as CSV or JSON
pykabu-calendar calendar 2026-02-10 -f csv
pykabu-calendar calendar 2026-02-10 -f json

# Export to file (format detected from extension)
pykabu-calendar calendar 2026-02-10 -o earnings.csv
pykabu-calendar calendar 2026-02-10 -o earnings.parquet
pykabu-calendar calendar 2026-02-10 -o earnings.db
```

### `check` — Health check sources

```bash
pykabu-calendar check
```

Output:

```
  sbi             ok     rows=42
  matsui          ok     rows=30
  tradersweb      FAIL   rows=0  error=timeout
```

### `lookup` — Single stock info

```bash
# Basic lookup (past earnings + inferred time)
pykabu-calendar lookup 7203

# Include IR page discovery
pykabu-calendar lookup 7203 --ir

# Show more past announcements
pykabu-calendar lookup 7203 --history 12
```

### `config` — Show configuration

```bash
pykabu-calendar config
```

### `--version`

```bash
pykabu-calendar --version
```
