"""
Matsui Securities source configuration.

Update these values when the site structure changes.
"""

# Base URL for earnings calendar
URL = "https://finance.matsui.co.jp/find-by-schedule/index"

# CSS selector for the data table
TABLE_SELECTOR = "table.m-table"

# CSS selector for result count (pagination)
RESULT_SELECTOR = "p.m-table-utils-result"

# Date format used by Matsui
DATE_FORMAT = "%Y/%m/%d"

# Column containing company name and code
NAME_CODE_COLUMN = "銘柄名(銘柄コード)"

# Regex patterns for extraction
CODE_PATTERN = r"\((\w+)\)"
NAME_PATTERN = r"^(.+?)\("

# Pagination settings
PER_PAGE = 100


def build_url(date: str, page: int = 1) -> str:
    """
    Build Matsui calendar URL.

    Args:
        date: Date in YYYY-MM-DD format
        page: Page number (1-indexed)

    Returns:
        Full URL with query parameters
    """
    year, month, day = date.split("-")
    return f"{URL}?date={year}/{int(month)}/{int(day)}&page={page}&per_page={PER_PAGE}"
