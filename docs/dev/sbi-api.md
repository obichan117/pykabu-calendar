# SBI Securities JSONP API

SBI's earnings calendar page at `sbisec.co.jp/ETGate/` renders data client-side
using JavaScript templates. The data comes from a JSONP API at `vc.iris.sbisec.co.jp`.

## Discovery

The page HTML contains JavaScript variables with API configuration:

```javascript
var FIXED_QS = '?hash=d78374a2dc5233aad540e55eb792d42d14b8a593&investor=visitor&callback=?';
var ANNOUNCE_INFO_PARAM = '?hash=d78374a2dc5233aad540e55eb792d42d14b8a593&type=delay';
var ANNOUNCE_CALENDAR_PARAM = '?hash=d78374a2dc5233aad540e55eb792d42d14b8a593&type=delay';
```

The `hash` is a 40-character SHA-1 hex string required for API authentication.
It appears to be static (same across sessions), but we extract it fresh each time
to handle potential rotation.

## Endpoints

### announcement_info_date.do (used)

Returns all earnings entries for a specific date. **No pagination** — returns
every entry in a single response.

```
GET https://vc.iris.sbisec.co.jp/calendar/settlement/stock/announcement_info_date.do
    ?hash=<40-char-hex>
    &type=delay
    &selectedDate=YYYYMMDD
    &callback=cb
```

### announcement_calendar_list.do (not used)

Returns the monthly calendar grid with daily counts. Not needed for our purposes.

## Response Format

JSONP with a callback wrapper. The inner object has **unquoted JavaScript keys**
(not valid JSON), requiring regex fixup before parsing.

```javascript
cb({
    "pageName": "searchCalendar",
    link : {
        "imageServer": "https://sbisec.akamaized.net/sbisec",
        "productLinkBase": "...",
        ...
    },
    "body" : [
        {
            "handling": "1",
            "date": "2026/02/10",
            "publishStatus": "予定",
            "time": "13:20<br>(予定)",
            "productCode": "7675",
            "productName": "セントラルフォレストグループ",
            "exchangeCode": "NGY",
            "type": "本決算",
            "progressStatus": "NODATA",
            "profitAndRate": "--<br>(<span class=''>--％</span>)",
            "estimate": "3,230",
            "consensus": "--",
            ...
        },
        ...
    ]
})
```

### Key Fields

| Field | Description | Example |
|-------|-------------|---------|
| `productCode` | Stock ticker code | `"7675"` |
| `productName` | Company name (full-width) | `"セントラルフォレストグループ"` |
| `time` | Announcement time with HTML | `"13:20<br>(予定)"` |
| `date` | Announcement date | `"2026/02/10"` or `"2026/02<br>上旬"` |
| `type` | Report type with possible HTML | `"本決算"`, `"3Q"`, `"中間<br>決算"` |
| `exchangeCode` | Exchange code | `"TKY"`, `"NGY"` |
| `publishStatus` | Publication status | `"予定"`, `"発表済"` |

### JSONP Parsing

The `link` key is unquoted, making the response invalid JSON. We handle this by:

1. Extracting just the `"body"` array via regex
2. Fixing unquoted keys with `re.sub(r"(\s)(\w+)\s*:", r'\1"\2":', text)`
3. Parsing the result as standard JSON

## Advantages Over Browser Scraping

| | Playwright (old) | JSONP API (new) |
|---|---|---|
| Entries | 187/318 (pagination breaks) | 318/318 (all) |
| Time | ~60s | ~2s |
| Dependencies | Playwright + Chromium | requests only |
| Reliability | Fragile (CSS selectors, buttons) | Stable (structured data) |
