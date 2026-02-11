"""
SBI Securities source configuration.

SBI's earnings calendar page loads data via a JSONP API at vc.iris.sbisec.co.jp.
The API requires a SHA-1 hash parameter embedded in the page HTML.
This replaces the previous Playwright-based approach with plain HTTP requests.

See api.md for full API documentation.
"""

import re

# Page URL (fetched to extract hash parameter)
PAGE_URL = "https://www.sbisec.co.jp/ETGate/"
PAGE_PARAMS = (
    "_ControlID=WPLETmgR001Control&"
    "_PageID=WPLETmgR001Mdtl20&"
    "_DataStoreID=DSWPLETmgR001Control&"
    "_ActionID=DefaultAID&"
    "burl=iris_economicCalendar&"
    "cat1=market&cat2=economicCalender&"
    "dir=tl1-cal%7Ctl2-schedule%7Ctl3-stock%7Ctl4-calsel%7Ctl9-{year}{month}%7Ctl10-{year}{month}{day}&"
    "file=index.html&getFlg=on"
)

# JSONP API endpoint (returns all entries for a given date, no pagination)
API_ENDPOINT = (
    "https://vc.iris.sbisec.co.jp/calendar/settlement/stock/announcement_info_date.do"
)

# Regex to extract hash from page HTML (appears in var FIXED_QS, ANNOUNCE_INFO_PARAM, etc.)
HASH_PATTERN = r"hash=([a-f0-9]{40})"

# Regex to extract time from API response, e.g. "13:20<br>(予定)"
TIME_PATTERN = r"(\d{1,2}:\d{2})"


def build_url(date: str) -> str:
    """
    Build SBI calendar page URL (used to extract the hash parameter).

    Args:
        date: Date in YYYY-MM-DD format

    Returns:
        Full page URL with query parameters
    """
    year, month, day = date.split("-")
    params = PAGE_PARAMS.format(year=year, month=month, day=day)
    return f"{PAGE_URL}?{params}"


def build_api_params(hash_value: str, date: str) -> dict:
    """
    Build query parameters for the JSONP API call.

    Args:
        hash_value: SHA-1 hash extracted from the page HTML
        date: Date in YYYY-MM-DD format

    Returns:
        Dict of query parameters
    """
    year, month, day = date.split("-")
    return {
        "hash": hash_value,
        "type": "delay",
        "selectedDate": f"{year}{month}{day}",
        "callback": "cb",
    }


def extract_hash(html: str) -> str | None:
    """
    Extract the hash parameter from SBI page HTML.

    The hash appears in JavaScript variables like:
        var FIXED_QS = '?hash=d78374a2dc5233aad540e55eb792d42d14b8a593&...';

    Args:
        html: Page HTML content

    Returns:
        40-character hex hash string, or None if not found
    """
    match = re.search(HASH_PATTERN, html)
    return match.group(1) if match else None
