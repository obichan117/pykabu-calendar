"""
Pytest configuration for pykabu-calendar tests.

All tests use live scraping - no mocks.
Uses dynamic dates to ensure tests work regardless of when they're run.
"""

import pytest
from datetime import datetime, timedelta

from pykabu_calendar.earnings.sources import MatsuiEarningsSource


def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (heavy network I/O: IR discovery, inference)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip slow tests unless --runslow is passed."""
    if config.getoption("--runslow", default=False):
        return

    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add command line options."""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def find_date_with_earnings(max_days=30, min_entries=5):
    """
    Find a future weekday with earnings data for testing.

    Searches up to max_days ahead (weekdays only) to find a date
    with >= min_entries earnings. Falls back to next weekday if all
    network calls fail (offline-safe).
    """
    today = datetime.now()
    try:
        matsui = MatsuiEarningsSource()
        for i in range(1, max_days + 1):
            target = today + timedelta(days=i)
            if target.weekday() >= 5:  # Skip weekends
                continue
            date_str = target.strftime("%Y-%m-%d")
            try:
                df = matsui.fetch(date_str)
                if len(df) >= min_entries:
                    return date_str
            except Exception:
                continue
    except Exception:
        pass
    # Fallback: next weekday (works offline)
    target = today + timedelta(days=1)
    while target.weekday() >= 5:
        target += timedelta(days=1)
    return target.strftime("%Y-%m-%d")


# Cache at module level for efficiency
_CACHED_TEST_DATE = None


@pytest.fixture(scope="session")
def test_date():
    """
    Fixture providing a future date with earnings data.

    Cached for the entire test session to avoid repeated lookups.
    """
    global _CACHED_TEST_DATE
    if _CACHED_TEST_DATE is None:
        _CACHED_TEST_DATE = find_date_with_earnings()
        print(f"\nUsing test date: {_CACHED_TEST_DATE}")
    return _CACHED_TEST_DATE


def get_test_date():
    """
    Function version for use outside fixtures.

    Returns cached date or finds one.
    """
    global _CACHED_TEST_DATE
    if _CACHED_TEST_DATE is None:
        _CACHED_TEST_DATE = find_date_with_earnings()
    return _CACHED_TEST_DATE
