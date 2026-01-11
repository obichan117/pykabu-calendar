"""
SBI Securities earnings calendar scraper.

Requires Playwright for JavaScript rendering.
"""

import logging
from io import StringIO

import pandas as pd

from .config import TIMEOUT, build_sbi_url

logger = logging.getLogger(__name__)


def fetch_sbi(date: str, timeout: int = TIMEOUT) -> pd.DataFrame:
    """
    Fetch earnings calendar from SBI Securities.

    Requires Playwright: pip install playwright && playwright install chromium

    Args:
        date: Target date in YYYY-MM-DD format
        timeout: Request timeout in seconds

    Returns:
        DataFrame with columns: [code, name, datetime]
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        )
        return pd.DataFrame(columns=["code", "name", "datetime"])

    url = build_sbi_url(date)
    logger.debug(f"Fetching {url}")

    all_rows = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=timeout * 1000)
            page.wait_for_selector("table.md-table06", timeout=10000)

            # Click "100件" to show more entries
            try:
                page.click("text=100件", timeout=5000)
                page.wait_for_timeout(1000)
            except Exception:
                pass  # Button may not exist

            # Paginate through all pages
            while True:
                table = page.query_selector("table.md-table06")
                if not table:
                    break

                html = table.inner_html()
                df = pd.read_html(StringIO(f"<table>{html}</table>"))[0]
                all_rows.append(df)

                # Try next page
                try:
                    next_btn = page.query_selector("text=次へ→")
                    if next_btn:
                        next_btn.click()
                        page.wait_for_timeout(1000)
                    else:
                        break
                except Exception:
                    break

            browser.close()

    except Exception as e:
        logger.error(f"SBI scraping failed: {e}")
        return pd.DataFrame(columns=["code", "name", "datetime"])

    if not all_rows:
        return pd.DataFrame(columns=["code", "name", "datetime"])

    raw_df = pd.concat(all_rows, ignore_index=True)
    return _parse_sbi(raw_df, date)


def _parse_sbi(raw_df: pd.DataFrame, date: str) -> pd.DataFrame:
    """Parse raw SBI DataFrame into standard format."""
    result = pd.DataFrame()

    # Parse date
    if "発表日" in raw_df.columns:
        result["_date"] = pd.to_datetime(raw_df["発表日"], format="%Y/%m/%d", errors="coerce")
        result["_date"] = result["_date"].fillna(pd.to_datetime(date))
    else:
        result["_date"] = pd.to_datetime(date)

    # Parse time (column may have space: "発表 時刻")
    time_col = None
    for col in raw_df.columns:
        if "時刻" in col:
            time_col = col
            break

    if time_col:
        # Format: "15:30 (予定)" -> "15:30"
        result["_time"] = raw_df[time_col].astype(str).str.extract(r"(\d{1,2}:\d{2})")[0]
    else:
        result["_time"] = pd.NA

    # Parse name and code
    name_col = None
    for col in raw_df.columns:
        if "銘柄" in col:
            name_col = col
            break

    if name_col:
        # Format: "トヨタ自動車 (7203)" or "オリオンビール (409A)"
        result["name"] = raw_df[name_col].str.extract(r"^(.+?)\s*\(")[0]
        result["code"] = raw_df[name_col].str.extract(r"\((\w+)\)")[0]
    else:
        result["name"] = None
        result["code"] = None

    # Combine date and time into datetime
    result["datetime"] = pd.to_datetime(
        result["_date"].astype(str) + " " + result["_time"].fillna("00:00").astype(str),
        errors="coerce",
    )

    # Set datetime to None where time was unknown
    result.loc[result["_time"].isna(), "datetime"] = pd.NaT

    return result[["code", "name", "datetime"]].dropna(subset=["code"])
