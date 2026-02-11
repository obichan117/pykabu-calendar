"""
SBI Securities earnings calendar scraper.

Uses SBI's JSONP API to fetch all earnings entries for a given date
in a single request. No browser automation required.

Flow:
  1. Fetch SBI page HTML with requests → extract hash parameter
  2. Call JSONP API with hash → get all entries (no pagination)
  3. Parse JSONP response → DataFrame[code, name, datetime]
"""

import json
import logging
import re

import pandas as pd

from ...core.fetch import fetch
from . import config

logger = logging.getLogger(__name__)

_EMPTY_DF = pd.DataFrame(columns=["code", "name", "datetime"])


def get_sbi(date: str) -> pd.DataFrame:
    """
    Get earnings calendar from SBI Securities.

    Args:
        date: Target date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: [code, name, datetime]
    """
    try:
        # Step 1: Fetch page to extract hash
        page_url = config.build_url(date)
        logger.debug(f"Fetching SBI page for hash: {page_url}")
        page_html = fetch(page_url)

        hash_value = config.extract_hash(page_html)
        if not hash_value:
            logger.error("Could not extract hash from SBI page")
            return _EMPTY_DF.copy()

        # Step 2: Call JSONP API
        params = config.build_api_params(hash_value, date)
        logger.debug(f"Calling SBI API with hash={hash_value[:8]}...")
        jsonp_text = fetch(config.API_ENDPOINT, params=params)

        # Step 3: Parse JSONP → list of dicts
        items = _parse_jsonp(jsonp_text)
        if not items:
            return _EMPTY_DF.copy()

        # Step 4: Build DataFrame
        return _build_dataframe(items, date)

    except Exception as e:
        logger.error(f"SBI scraping failed: {e}")
        return _EMPTY_DF.copy()


def _parse_jsonp(text: str) -> list[dict]:
    """
    Parse JSONP response into a list of dicts.

    The response is a JSONP callback wrapping a JS object with unquoted keys.
    We extract the "body" array and fix unquoted keys to make it valid JSON.
    """
    # Extract body array content
    body_match = re.search(r'"body"\s*:\s*\[(.*?)\]\s*\}', text, re.DOTALL)
    if not body_match:
        logger.warning("Could not find body array in JSONP response")
        return []

    items_str = "[" + body_match.group(1) + "]"

    # Fix unquoted JS keys: word followed by colon → add quotes
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

        # Extract time from "13:20<br>(予定)"
        time_match = re.search(config.TIME_PATTERN, time_raw)
        if time_match:
            dt = pd.Timestamp(f"{date} {time_match.group(1)}")
        else:
            dt = pd.NaT

        rows.append({"code": code, "name": name, "datetime": dt})

    if not rows:
        return _EMPTY_DF.copy()

    return pd.DataFrame(rows)
