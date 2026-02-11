"""SBI Securities earnings calendar source.

Uses SBI's JSONP API to fetch all earnings entries for a given date
in a single request. No browser automation required.

Flow:
  1. Fetch SBI page HTML with requests -> extract hash parameter
  2. Call JSONP API with hash -> get all entries (no pagination)
  3. Parse JSONP response -> DataFrame[code, name, datetime]
"""

import json
import logging
import re

import pandas as pd

from ...core.fetch import fetch
from ..base import EarningsSource, load_config

logger = logging.getLogger(__name__)

_config = load_config(__file__)

_EMPTY_DF = pd.DataFrame(columns=["code", "name", "datetime"])


def build_url(date: str) -> str:
    """Build SBI calendar page URL (used to extract the hash parameter).

    Args:
        date: Date in YYYY-MM-DD format

    Returns:
        Full page URL with query parameters
    """
    year, month, day = date.split("-")
    params = _config["page_params"].format(year=year, month=month, day=day)
    return f"{_config['page_url']}?{params}"


def build_api_params(hash_value: str, date: str) -> dict:
    """Build query parameters for the JSONP API call.

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
    """Extract the hash parameter from SBI page HTML.

    Args:
        html: Page HTML content

    Returns:
        40-character hex hash string, or None if not found
    """
    match = re.search(_config["hash_pattern"], html)
    return match.group(1) if match else None


# --- Internal helpers ---

def _parse_jsonp(text: str) -> list[dict]:
    """Parse JSONP response into a list of dicts."""
    body_match = re.search(r'"body"\s*:\s*\[(.*?)\]\s*\}', text, re.DOTALL)
    if not body_match:
        logger.warning("Could not find body array in JSONP response")
        return []

    items_str = "[" + body_match.group(1) + "]"
    items_str = re.sub(r"(\s)(\w+)\s*:", r'\1"\2":', items_str)

    try:
        return json.loads(items_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSONP body: {e}")
        return []


def _build_dataframe(items: list[dict], date: str) -> pd.DataFrame:
    """Build DataFrame from parsed API items."""
    rows = []
    for item in items:
        code = item.get("productCode", "")
        name = item.get("productName", "")
        time_raw = item.get("time", "")

        if not code:
            continue

        time_match = re.search(_config["time_pattern"], time_raw)
        if time_match:
            dt = pd.Timestamp(f"{date} {time_match.group(1)}")
        else:
            dt = pd.NaT

        rows.append({"code": code, "name": name, "datetime": dt})

    if not rows:
        return _EMPTY_DF.copy()

    return pd.DataFrame(rows)


# --- EarningsSource implementation ---

class SBIEarningsSource(EarningsSource):
    """SBI Securities earnings source (JSONP API)."""

    _config = _config

    @property
    def name(self) -> str:
        return "sbi"

    def _fetch(self, date: str) -> pd.DataFrame:
        try:
            page_url = build_url(date)
            logger.debug(f"Fetching SBI page for hash: {page_url}")
            page_html = fetch(page_url)

            hash_value = extract_hash(page_html)
            if not hash_value:
                logger.error("Could not extract hash from SBI page")
                return _EMPTY_DF.copy()

            params = build_api_params(hash_value, date)
            logger.debug(f"Calling SBI API with hash={hash_value[:8]}...")
            jsonp_text = fetch(_config["api_endpoint"], params=params)

            items = _parse_jsonp(jsonp_text)
            if not items:
                return _EMPTY_DF.copy()

            return _build_dataframe(items, date)

        except Exception as e:
            logger.error(f"SBI scraping failed: {e}")
            return _EMPTY_DF.copy()
