"""
SBI Securities source configuration.

Update these values when the site structure changes.

Note: SBI requires browser automation (Playwright) because
it uses JavaScript templating to render data.
"""

# Base URL
URL = "https://www.sbisec.co.jp/ETGate/"

# URL parameters template
URL_PARAMS = (
    "_ControlID=WPLETmgR001Control&"
    "_PageID=WPLETmgR001Mdtl20&"
    "_DataStoreID=DSWPLETmgR001Control&"
    "_ActionID=DefaultAID&"
    "burl=iris_economicCalendar&"
    "cat1=market&cat2=economicCalender&"
    "dir=tl1-cal%7Ctl2-schedule%7Ctl3-stock%7Ctl4-calsel%7Ctl9-{year}{month}%7Ctl10-{year}{month}{day}&"
    "file=index.html&getFlg=on"
)

# CSS selector for the data table
TABLE_SELECTOR = "table.md-table06"

# Button text for pagination
VIEW_ALL_BUTTON = "100件"
NEXT_BUTTON = "次へ→"

# Date format
DATE_FORMAT = "%Y/%m/%d"

# Column patterns (SBI has space in column name: "発表 時刻")
TIME_COLUMN_PATTERN = "時刻"
NAME_COLUMN_PATTERN = "銘柄"

# Regex patterns
CODE_PATTERN = r"\((\w+)\)"
NAME_PATTERN = r"^(.+?)\s*\("
TIME_PATTERN = r"(\d{1,2}:\d{2})"


def build_url(date: str) -> str:
    """
    Build SBI calendar URL.

    Args:
        date: Date in YYYY-MM-DD format

    Returns:
        Full URL with query parameters
    """
    year, month, day = date.split("-")
    params = URL_PARAMS.format(year=year, month=month, day=day)
    return f"{URL}?{params}"
