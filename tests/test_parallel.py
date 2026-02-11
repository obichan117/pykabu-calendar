"""Tests for parallel execution utilities."""

import time

from pykabu_calendar.core.parallel import run_parallel


class TestRunParallel:
    """Tests for run_parallel function."""

    def test_empty_tasks(self):
        """Empty tasks dict should return empty results."""
        assert run_parallel({}) == {}

    def test_single_task(self):
        """Single task should return its result."""
        results = run_parallel({"a": lambda: 42})
        assert results == {"a": 42}

    def test_multiple_tasks(self):
        """Multiple tasks should all return results."""
        results = run_parallel({
            "a": lambda: 1,
            "b": lambda: 2,
            "c": lambda: 3,
        })
        assert results == {"a": 1, "b": 2, "c": 3}

    def test_failed_task_omitted(self):
        """Failed tasks should be omitted from results."""
        def fail():
            raise ValueError("boom")

        results = run_parallel({
            "good": lambda: 42,
            "bad": fail,
        })
        assert results == {"good": 42}
        assert "bad" not in results

    def test_all_tasks_fail(self):
        """All tasks failing should return empty dict."""
        def fail():
            raise ValueError("boom")

        results = run_parallel({"a": fail, "b": fail})
        assert results == {}

    def test_tasks_run_concurrently(self):
        """Tasks should run concurrently, not sequentially."""
        def slow():
            time.sleep(0.1)
            return True

        start = time.monotonic()
        results = run_parallel({
            "a": slow,
            "b": slow,
            "c": slow,
        }, max_workers=3)
        elapsed = time.monotonic() - start

        assert len(results) == 3
        # 3 tasks sleeping 0.1s each should take ~0.1s, not ~0.3s
        assert elapsed < 0.25

    def test_max_workers_respected(self):
        """Should work with max_workers=1 (sequential)."""
        results = run_parallel(
            {"a": lambda: 1, "b": lambda: 2},
            max_workers=1,
        )
        assert results == {"a": 1, "b": 2}
