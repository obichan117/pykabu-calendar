"""
Generic fetch utilities.

This module handles HTTP requests and browser automation.
It returns raw content (str, dict, bytes) - never DataFrames.
"""

import logging
import threading
from typing import Optional

import requests

from ..config import HEADERS, TIMEOUT

logger = logging.getLogger(__name__)

_thread_local = threading.local()


def get_session() -> requests.Session:
    """Get a configured requests session (one per thread)."""
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(HEADERS)
        _thread_local.session = session
    return session


def fetch(url: str, timeout: int = TIMEOUT, **kwargs) -> str:
    """
    Fetch URL content using requests.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to requests.get()

    Returns:
        HTML content as string

    Raises:
        requests.RequestException: If request fails
    """
    logger.debug(f"Fetching {url}")
    session = get_session()

    response = session.get(url, timeout=timeout, **kwargs)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    return response.text


def fetch_browser(url: str, wait_selector: str, timeout: int = TIMEOUT) -> str:
    """
    Fetch URL content using Playwright browser.

    Use this for JavaScript-rendered pages.

    Args:
        url: URL to fetch
        wait_selector: CSS selector to wait for before extracting HTML
        timeout: Navigation timeout in seconds

    Returns:
        HTML content as string

    Raises:
        ImportError: If Playwright is not installed
        Exception: If browser automation fails
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    logger.debug(f"Fetching {url} with browser")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=timeout * 1000)
        page.wait_for_selector(wait_selector, timeout=10000)

        html = page.content()
        browser.close()

    return html


def fetch_browser_with_pagination(
    url: str,
    table_selector: str,
    next_button_text: Optional[str] = None,
    view_all_text: Optional[str] = None,
    timeout: int = TIMEOUT,
) -> list[str]:
    """
    Fetch paginated content using Playwright browser.

    Args:
        url: URL to fetch
        table_selector: CSS selector for the data table
        next_button_text: Text of "next page" button (optional)
        view_all_text: Text of "view all" button to click first (optional)
        timeout: Navigation timeout in seconds

    Returns:
        List of HTML strings (one per page)
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    logger.debug(f"Fetching {url} with browser (paginated)")
    pages = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=timeout * 1000)
        page.wait_for_selector(table_selector, timeout=10000)

        # Click "view all" if provided
        if view_all_text:
            try:
                page.click(f"text={view_all_text}", timeout=5000)
                page.wait_for_timeout(1000)
            except Exception:
                pass  # Button may not exist

        # Paginate
        while True:
            table = page.query_selector(table_selector)
            if table:
                pages.append(f"<table>{table.inner_html()}</table>")

            if not next_button_text:
                break

            try:
                next_btn = page.query_selector(f"text={next_button_text}")
                if next_btn:
                    next_btn.click()
                    page.wait_for_timeout(1000)
                else:
                    break
            except Exception:
                break

        browser.close()

    return pages
