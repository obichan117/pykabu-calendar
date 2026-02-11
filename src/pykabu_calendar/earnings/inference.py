"""Historical pattern inference for earnings announcement times.

Uses pykabutan to fetch past earnings announcement datetimes.
"""

import logging
from collections import Counter

import pandas as pd
import pykabutan as pk
import requests

logger = logging.getLogger(__name__)

# Confidence thresholds for historical pattern inference
_HIGH_CONFIDENCE_RATIO = 0.75
_MEDIUM_CONFIDENCE_RATIO = 0.5

# TSE trading session boundaries (minutes from midnight)
_MORNING_OPEN = 540  # 9:00
_MORNING_CLOSE = 690  # 11:30
_AFTERNOON_OPEN = 750  # 12:30
_AFTERNOON_CLOSE = 930  # 15:30


def get_past_earnings(code: str, n_recent: int = 8) -> list[pd.Timestamp]:
    """Get past earnings announcement datetimes using pykabutan.

    Args:
        code: Stock code (e.g., "7203")
        n_recent: Number of recent announcements to fetch

    Returns:
        List of datetime objects for past earnings announcements
    """
    try:
        ticker = pk.Ticker(code)
        df = ticker.news(mode="earnings")

        if df.empty:
            return []

        datetimes = df["datetime"].head(n_recent).tolist()
        return [pd.Timestamp(dt) for dt in datetimes]

    except (ValueError, AttributeError, requests.RequestException) as e:
        logger.warning(f"Failed to get past earnings for {code}: {e}")
        return []


def infer_datetime(
    code: str,
    date: str,
    past_datetimes: list[pd.Timestamp] | None = None,
) -> tuple[pd.Timestamp | None, str, list[pd.Timestamp]]:
    """Infer announcement datetime from historical patterns.

    Args:
        code: Stock code
        date: Target date in YYYY-MM-DD format
        past_datetimes: Optional pre-fetched past datetimes

    Returns:
        Tuple of (inferred_datetime, confidence, past_datetimes)
        - inferred_datetime: Predicted datetime or None
        - confidence: "high", "medium", "low", or "none"
        - past_datetimes: List of past datetimes used for inference
    """
    if past_datetimes is None:
        past_datetimes = get_past_earnings(code)

    if not past_datetimes:
        return None, "none", []

    past_times = [dt.strftime("%H:%M") for dt in past_datetimes]
    unique_times = list(set(past_times))

    time_counts = Counter(past_times)
    most_common_time, most_common_count = time_counts.most_common(1)[0]
    ratio = most_common_count / len(past_times)

    if len(unique_times) == 1 or ratio >= _HIGH_CONFIDENCE_RATIO:
        confidence = "high"
    elif ratio >= _MEDIUM_CONFIDENCE_RATIO:
        confidence = "medium"
    else:
        confidence = "low"

    try:
        inferred_dt = pd.Timestamp(f"{date} {most_common_time}")
    except (ValueError, TypeError):
        inferred_dt = pd.NaT
        confidence = "none"

    return inferred_dt, confidence, past_datetimes


def is_during_trading_hours(dt: pd.Timestamp) -> bool:
    """Check if datetime is during trading hours (zaraba).

    Trading hours (open inclusive, close exclusive):
    - Morning: 9:00 <= t < 11:30
    - Afternoon: 12:30 <= t < 15:30
    """
    if pd.isna(dt):
        return False

    minutes = dt.hour * 60 + dt.minute

    if _MORNING_OPEN <= minutes < _MORNING_CLOSE:
        return True

    if _AFTERNOON_OPEN <= minutes < _AFTERNOON_CLOSE:
        return True

    return False
