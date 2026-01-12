"""
Tradersweb source configuration.

Update these values when the site structure changes.
"""

# Base URL for earnings calendar
URL = "https://www.traders.co.jp/market_jp/earnings_calendar"

# CSS selector for the data table
TABLE_SELECTOR = "table.data_table"

# Date format (Tradersweb uses MM/DD, needs year prepended)
DATE_FORMAT = "%Y/%m/%d"

# Column patterns
NAME_COLUMN_PATTERN = "銘柄名"  # Column name contains this

# Regex patterns for extraction
CODE_PATTERN = r"\((\w+)/"
NAME_PATTERN = r"^([^(]+)"


def build_url(date: str) -> str:
    """
    Build Tradersweb calendar URL.

    Args:
        date: Date in YYYY-MM-DD format

    Returns:
        Full URL with query parameters
    """
    year, month, day = date.split("-")
    return f"{URL}/all/all/1?term={year}/{month}/{day}"
