"""Historical pattern inference for earnings announcement times.

Uses pykabutan to fetch past earnings announcement datetimes.
"""

import logging
from collections import Counter

import pandas as pd
import pykabutan as pk

logger = logging.getLogger(__name__)


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

    except Exception as e:
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

    if len(unique_times) == 1 or ratio >= 0.75:
        confidence = "high"
    elif ratio >= 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    try:
        inferred_dt = pd.Timestamp(f"{date} {most_common_time}")
    except Exception:
        inferred_dt = None
        confidence = "none"

    return inferred_dt, confidence, past_datetimes


def is_during_trading_hours(dt: pd.Timestamp) -> bool:
    """Check if datetime is during trading hours (zaraba).

    Trading hours:
    - Morning: 9:00 - 11:30
    - Afternoon: 12:30 - 15:30
    """
    if pd.isna(dt):
        return False

    minutes = dt.hour * 60 + dt.minute

    if 540 <= minutes <= 690:
        return True

    if 750 <= minutes <= 930:
        return True

    return False
