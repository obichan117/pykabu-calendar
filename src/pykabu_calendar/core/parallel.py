"""Parallel execution utilities."""

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

logger = logging.getLogger(__name__)


def run_parallel(
    tasks: dict[str, Callable[[], Any]],
    max_workers: int = 4,
) -> dict[str, Any]:
    """Run multiple callables in parallel using threads.

    Args:
        tasks: Mapping of name -> callable. Each callable takes no arguments.
        max_workers: Maximum number of concurrent threads.

    Returns:
        Mapping of name -> result for tasks that succeeded.
        Failed tasks are logged at WARNING and omitted from results.
    """
    if not tasks:
        return {}

    results: dict[str, Any] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_name = {
            executor.submit(fn): name for name, fn in tasks.items()
        }

        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                results[name] = future.result()
            except Exception as e:
                logger.warning(f"[{name}] failed: {e}")

    return results
