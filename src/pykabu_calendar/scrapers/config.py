"""
Scraper configuration.

All URLs, headers, and settings in ONE place for easy maintenance.
"""

import requests

# Modern Chrome User-Agent (Chrome 131 on Windows 11)
# This is generic enough to work on most sites without being blocked
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# Default request headers
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# Default timeout in seconds
TIMEOUT = 30

# =============================================================================
# Source URLs - Edit these when sites change their structure
# =============================================================================

# SBI Securities
SBI_BASE_URL = "https://www.sbisec.co.jp/ETGate/"
SBI_CALENDAR_PARAMS = (
    "_ControlID=WPLETmgR001Control&"
    "_PageID=WPLETmgR001Mdtl20&"
    "_DataStoreID=DSWPLETmgR001Control&"
    "_ActionID=DefaultAID&"
    "burl=iris_economicCalendar&"
    "cat1=market&cat2=economicCalender&"
    "dir=tl1-cal%7Ctl2-schedule%7Ctl3-stock%7Ctl4-calsel%7Ctl9-{year}{month}%7Ctl10-{year}{month}{day}&"
    "file=index.html&getFlg=on"
)

# Matsui Securities
MATSUI_BASE_URL = "https://finance.matsui.co.jp/find-by-schedule/index"
MATSUI_PARAMS = "date={year}/{month}/{day}&page={page}&per_page=100"

# Tradersweb
TRADERSWEB_BASE_URL = "https://www.traders.co.jp/market_jp/earnings_calendar"
TRADERSWEB_PARAMS = "all/all/1?term={year}/{month}/{day}"


# =============================================================================
# Helper functions
# =============================================================================

_session = None


def get_session() -> requests.Session:
    """Get a configured requests session (singleton)."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(HEADERS)
    return _session


def build_sbi_url(date: str) -> str:
    """Build SBI calendar URL for a given date (YYYY-MM-DD)."""
    year, month, day = date.split("-")
    params = SBI_CALENDAR_PARAMS.format(year=year, month=month, day=day)
    return f"{SBI_BASE_URL}?{params}"


def build_matsui_url(date: str, page: int = 1) -> str:
    """Build Matsui calendar URL for a given date (YYYY-MM-DD)."""
    year, month, day = date.split("-")
    params = MATSUI_PARAMS.format(year=year, month=int(month), day=int(day), page=page)
    return f"{MATSUI_BASE_URL}?{params}"


def build_tradersweb_url(date: str) -> str:
    """Build Tradersweb calendar URL for a given date (YYYY-MM-DD)."""
    year, month, day = date.split("-")
    params = TRADERSWEB_PARAMS.format(year=year, month=month, day=day)
    return f"{TRADERSWEB_BASE_URL}/{params}"
