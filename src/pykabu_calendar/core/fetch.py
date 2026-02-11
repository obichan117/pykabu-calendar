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
_session_version = 0
_version_lock = threading.Lock()


def _reset_sessions() -> None:
    """Bump version so all threads create fresh sessions on next access."""
    global _session_version
    with _version_lock:
        _session_version += 1


on_configure(_reset_sessions)


def get_session() -> requests.Session:
    """Get a configured requests session (one per thread)."""
    local_ver = getattr(_thread_local, "version", -1)
    if local_ver != _session_version:
        session = requests.Session()
        session.headers.update(get_settings().headers)
        _thread_local.session = session
        _thread_local.version = _session_version
    return _thread_local.session


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


def fetch_safe(url: str, timeout: int | None = None) -> str | None:
    """Fetch URL content, returning None on failure instead of raising.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds (default: from settings)

    Returns:
        HTML content as string, or None if request failed
    """
    try:
        return fetch(url, timeout=timeout)
    except requests.RequestException as e:
        logger.debug(f"Failed to fetch {url}: {e}")
        return None
