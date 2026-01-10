"""
Historical pattern inference for earnings announcement times.

Infers announcement time based on past earnings announcement patterns
from kabutan.jp news data.
"""

import logging
from datetime import datetime
from io import StringIO
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def get_past_earnings_times(code: str, n_recent: int = 8) -> list[str]:
    """
    Get past earnings announcement times from kabutan.jp.

    Args:
        code: Stock code (e.g., "7203")
        n_recent: Number of recent announcements to fetch

    Returns:
        List of time strings (e.g., ["15:00", "15:00", "13:30"])
    """
    url = f"https://kabutan.jp/stock/news?code={code}&nmode=2"

    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = "utf-8"

        # Parse the news table
        dfs = pd.read_html(StringIO(response.text))

        # The earnings news table is typically the 4th table (index 3)
        # Format: [datetime, news_type, news_title]
        if len(dfs) < 4:
            logger.warning(f"Not enough tables found for {code}")
            return []

        df = dfs[3]
        if df.shape[1] != 3:
            logger.warning(f"Unexpected table format for {code}")
            return []

        df.columns = ["datetime", "news_type", "news_title"]

        # Parse datetime: "25/01/20 15:00" -> datetime
        df["datetime"] = pd.to_datetime(df["datetime"], format="%y/%m/%d %H:%M", errors="coerce")

        # Filter for earnings announcements (決算)
        earnings_df = df[df["news_type"] == "決算"]

        if earnings_df.empty:
            return []

        # Extract times from most recent announcements
        times = earnings_df["datetime"].head(n_recent).dt.strftime("%H:%M").tolist()
        return times

    except Exception as e:
        logger.error(f"Failed to get past earnings for {code}: {e}")
        return []


def infer_time_from_history(
    code: str, past_times: Optional[list[str]] = None
) -> tuple[Optional[str], str]:
    """
    Infer announcement time from historical patterns.

    Args:
        code: Stock code
        past_times: Optional pre-fetched past times

    Returns:
        Tuple of (inferred_time, confidence)
        - inferred_time: "HH:MM" string or None
        - confidence: "high", "medium", or "low"
    """
    if past_times is None:
        past_times = get_past_earnings_times(code)

    if not past_times:
        return None, "none"

    # Analyze patterns
    unique_times = list(set(past_times))

    # All same time -> high confidence
    if len(unique_times) == 1:
        return unique_times[0], "high"

    # Mostly same time (>= 75%)
    from collections import Counter

    time_counts = Counter(past_times)
    most_common_time, most_common_count = time_counts.most_common(1)[0]

    if most_common_count / len(past_times) >= 0.75:
        return most_common_time, "high"

    if most_common_count / len(past_times) >= 0.5:
        return most_common_time, "medium"

    # No clear pattern
    return most_common_time, "low"


def is_during_trading_hours(time_str: str) -> bool:
    """
    Check if time is during trading hours (zaraba).

    Trading hours:
    - Morning: 9:00 - 11:30
    - Afternoon: 12:30 - 15:30
    """
    if not time_str:
        return False

    try:
        hour, minute = map(int, time_str.split(":"))
        time_minutes = hour * 60 + minute

        # Morning session: 9:00 - 11:30 (540 - 690 minutes)
        if 540 <= time_minutes <= 690:
            return True

        # Afternoon session: 12:30 - 15:30 (750 - 930 minutes)
        if 750 <= time_minutes <= 930:
            return True

        return False
    except (ValueError, AttributeError):
        return False


def is_time_significant(time_str: str) -> bool:
    """
    Check if knowing the exact time is significant for trading.

    Time is significant if it's during trading hours or just before close.
    Time is NOT significant if it's after 15:30 (after close).
    """
    if not time_str:
        return True  # Unknown time is significant

    try:
        hour, minute = map(int, time_str.split(":"))
        time_minutes = hour * 60 + minute

        # After 15:30 (930 minutes) is not significant
        return time_minutes <= 930
    except (ValueError, AttributeError):
        return True


def add_historical_inference(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add time_inferred column to calendar DataFrame.

    Args:
        df: Calendar DataFrame with 'code' column

    Returns:
        DataFrame with added 'time_inferred' and 'inference_confidence' columns
    """
    if "code" not in df.columns:
        df["time_inferred"] = None
        df["inference_confidence"] = None
        return df

    # Process each unique code
    unique_codes = df["code"].unique()
    logger.info(f"Inferring times for {len(unique_codes)} companies...")

    results = {}
    for code in unique_codes:
        try:
            time, confidence = infer_time_from_history(str(code))
            results[code] = (time, confidence)
        except Exception as e:
            logger.warning(f"Failed to infer time for {code}: {e}")
            results[code] = (None, "error")

    df["time_inferred"] = df["code"].map(lambda c: results.get(c, (None, None))[0])
    df["inference_confidence"] = df["code"].map(lambda c: results.get(c, (None, None))[1])

    return df
