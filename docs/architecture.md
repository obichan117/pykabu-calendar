# Architecture

This page describes the internal architecture of pykabu-calendar: how data flows through the system, how modules depend on each other, and how IR discovery works.

## Module Layers

The codebase follows a strict three-layer architecture. High-level modules depend on low-level ones, never the reverse.

```mermaid
graph TD
    subgraph "Public API"
        A["__init__.py<br/>get_calendar, configure, export_to_*"]
    end

    subgraph "Domain Layer: earnings/"
        B["calendar.py<br/>Aggregator: merge, rank, select"]
        C["sources/<br/>SBI · Matsui · Tradersweb"]
        D["ir/<br/>Discovery · Parser · Cache"]
        E["inference.py<br/>Historical patterns"]
        F["base.py<br/>EarningsSource ABC"]
    end

    subgraph "Infrastructure"
        G["core/<br/>fetch · parse · parallel · io"]
        H["config.py + config.yaml<br/>Settings singleton"]
        I["llm/<br/>LLMClient ABC · Gemini"]
    end

    A --> B
    B --> C
    B --> D
    B --> E
    C --> F
    C --> G
    D --> G
    D --> I
    E -.->|pykabutan| EXT["External: pykabutan"]
    F --> G
    G --> H
    I --> H

    style A fill:#4a86c8,color:#fff
    style B fill:#6aa84f,color:#fff
    style G fill:#e69138,color:#fff
    style H fill:#e69138,color:#fff
    style I fill:#e69138,color:#fff
```

**Key rules:**

- `core/` never imports from `earnings/` or `llm/`
- `earnings/` never imports from `llm/` directly (only `ir/` does, for fallback)
- `config.py` is imported by everything but imports nothing from the project
- `llm/` is optional — the system works without it (rule-based only)

## Data Flow

When you call `get_calendar("2026-02-10")`, here's what happens:

```mermaid
flowchart LR
    subgraph "1. Fetch"
        SBI["SBI<br/>JSONP API"]
        MAT["Matsui<br/>HTML scrape"]
        TW["Tradersweb<br/>HTML scrape"]
    end

    subgraph "2. Merge"
        MERGE["Outer join<br/>on stock code"]
    end

    subgraph "3. Enrich"
        HIST["Historical<br/>inference"]
        IR["IR page<br/>discovery"]
    end

    subgraph "4. Rank"
        RANK["Build candidates<br/>Select best datetime<br/>Assign confidence"]
    end

    SBI -->|parallel| MERGE
    MAT -->|parallel| MERGE
    TW -->|parallel| MERGE
    MERGE --> HIST
    HIST -->|parallel per stock| IR
    IR --> RANK
    RANK --> OUT["DataFrame"]
```

### Step-by-step

| Step | Function | What happens |
|------|----------|--------------|
| **1. Fetch** | `run_parallel(tasks)` | All sources fetched concurrently via `ThreadPoolExecutor` |
| **2. Merge** | `_merge_sources()` | Outer join on `code` column, each source gets a `{name}_datetime` column |
| **3a. History** | `_add_history()` | For each stock, fetch past earnings times via pykabutan and infer most likely time |
| **3b. IR** | `_add_ir()` | For each stock, discover IR page and parse announcement datetime (cached) |
| **4. Rank** | `_build_candidates()` | Apply priority rules, build candidate list, assign confidence level |

### Confidence Levels

```mermaid
flowchart TD
    START["Has IR datetime?"]
    START -->|Yes| HIGHEST["highest"]
    START -->|No| CHECK2["Inferred matches<br/>a scraper?"]
    CHECK2 -->|Yes| HIGH1["high"]
    CHECK2 -->|No| CHECK3["2+ scrapers<br/>agree on time?"]
    CHECK3 -->|Yes| HIGH2["high"]
    CHECK3 -->|No| CHECK4["Multiple sources<br/>available?"]
    CHECK4 -->|Yes| MEDIUM["medium"]
    CHECK4 -->|No| LOW["low"]

    style HIGHEST fill:#0b8043,color:#fff
    style HIGH1 fill:#6aa84f,color:#fff
    style HIGH2 fill:#6aa84f,color:#fff
    style MEDIUM fill:#f1c232,color:#000
    style LOW fill:#cc4125,color:#fff
```

## IR Discovery Pipeline

The IR discovery module finds company investor relations pages through a 3-stage fallback chain:

```mermaid
sequenceDiagram
    participant Cal as calendar.py
    participant Disc as discovery.py
    participant PK as pykabutan
    participant Web as Company Website
    participant LLM as Gemini LLM
    participant Parse as parser.py
    participant Cache as cache.py

    Cal->>Cache: get_cached(code)
    alt Cache hit (not expired)
        Cache-->>Cal: cached datetime
    else Cache miss
        Cal->>Disc: discover_ir_page(code)
        Disc->>PK: Ticker(code).profile.website
        PK-->>Disc: https://company.co.jp

        Note over Disc,Web: Stage 1: Pattern matching
        Disc->>Web: HEAD /ir/calendar/, /ir/, /investor/ ...
        alt URL exists
            Web-->>Disc: 200 OK
        else No pattern match
            Note over Disc,Web: Stage 2: Homepage link search
            Disc->>Web: GET homepage HTML
            Web-->>Disc: HTML content
            Disc->>Disc: Find IR link (rule-based)
            alt Link found
                Disc-->>Disc: IR URL
            else No link found
                Note over Disc,LLM: Stage 3: LLM fallback
                Disc->>LLM: "Find IR page link in this HTML"
                LLM-->>Disc: IR URL
            end
        end

        Disc-->>Cal: IRPageInfo

        Cal->>Parse: parse_earnings_datetime(url)
        Parse->>Web: GET IR page HTML
        Web-->>Parse: HTML content
        Parse->>Parse: Rule-based parsing<br/>(Japanese date/time patterns)
        alt Parsed successfully
            Parse-->>Cal: EarningsInfo
        else Rule-based failed
            Parse->>LLM: "Extract earnings datetime"
            LLM-->>Parse: ISO datetime
            Parse-->>Cal: EarningsInfo
        end

        Cal->>Cache: save_cache(code, url, datetime)
    end
```

## Source Implementation Pattern

Each scraper follows the same pattern: a Python file for logic + a YAML file for configuration.

```mermaid
classDiagram
    class EarningsSource {
        <<abstract>>
        +name: str*
        +fetch(date: str) DataFrame
        +check() dict
        #_fetch(date: str) DataFrame*
    }

    class SBIEarningsSource {
        +name = "sbi"
        -_config: dict
        #_fetch(date) DataFrame
    }

    class MatsuiEarningsSource {
        +name = "matsui"
        -_config: dict
        #_fetch(date) DataFrame
    }

    class TraderswebEarningsSource {
        +name = "tradersweb"
        -_config: dict
        #_fetch(date) DataFrame
    }

    EarningsSource <|-- SBIEarningsSource
    EarningsSource <|-- MatsuiEarningsSource
    EarningsSource <|-- TraderswebEarningsSource
```

**Convention:** The YAML file has the same stem as the Python file (`sbi.py` + `sbi.yaml`). YAML contains URLs, CSS selectors, regex patterns, and health check config. Python contains fetch/parse logic.

## File Map

```
src/pykabu_calendar/           # ~2,300 lines total
├── __init__.py                # Public API re-exports
├── config.py                  # Settings dataclass + configure()
├── config.yaml                # Default values (timeout, LLM params, etc.)
├── core/                      # Reusable infrastructure (325 lines)
│   ├── fetch.py               # HTTP: fetch(), fetch_safe(), get_session()
│   ├── parse.py               # HTML→DataFrame: parse_table(), combine_datetime()
│   ├── parallel.py            # run_parallel() — ThreadPoolExecutor wrapper
│   └── io.py                  # Export: CSV, Parquet, SQLite
├── earnings/                  # Domain logic (1,505 lines)
│   ├── base.py                # EarningsSource ABC + load_config()
│   ├── calendar.py            # get_calendar() — merge, enrich, rank
│   ├── inference.py           # Historical pattern inference via pykabutan
│   ├── sources/               # Scraper implementations
│   │   ├── sbi.py + .yaml    # SBI Securities (JSONP API)
│   │   ├── matsui.py + .yaml # Matsui Securities (HTML + pagination)
│   │   └── tradersweb.py + .yaml  # Tradersweb (HTML single-page)
│   └── ir/                    # Company IR page discovery
│       ├── discovery.py       # 3-stage fallback: pattern → homepage → LLM
│       ├── parser.py          # Japanese date/time extraction (rule → LLM)
│       ├── patterns.py        # IR URL patterns + keyword lists
│       └── cache.py           # Thread-safe JSON cache (~/.pykabu_calendar/)
└── llm/                       # Optional LLM layer (328 lines)
    ├── base.py                # LLMClient ABC + find_link/extract_datetime
    └── gemini.py              # Google Gemini free tier implementation
```
