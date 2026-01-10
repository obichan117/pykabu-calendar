"""
Pytest configuration for pykabu-calendar tests.

All tests use live scraping - no mocks.
"""

import pytest


def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (require browser automation)"
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
