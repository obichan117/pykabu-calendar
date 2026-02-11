"""
Generic fetch utilities.

This module handles HTTP requests.
It returns raw content (str, dict, bytes) - never DataFrames.
"""

import logging
import threading

import requests

from ..config import get_settings, on_configure

logger = logging.getLogger(__name__)

_thread_local = threading.local()


def _reset_sessions() -> None:
    """Clear thread-local sessions so new settings take effect."""
    _thread_local.__dict__.clear()


on_configure(_reset_sessions)


def get_session() -> requests.Session:
    """Get a configured requests session (one per thread)."""
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(get_settings().headers)
        _thread_local.session = session
    return session


def fetch(url: str, timeout: int | None = None, **kwargs) -> str:
    """
    Fetch URL content using requests.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds (default: from settings)
        **kwargs: Additional arguments passed to requests.get()

    Returns:
        HTML content as string

    Raises:
        requests.RequestException: If request fails
    """
    if timeout is None:
        timeout = get_settings().timeout
    logger.debug(f"Fetching {url}")
    session = get_session()

    response = session.get(url, timeout=timeout, **kwargs)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    return response.text
