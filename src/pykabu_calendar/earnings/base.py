"""EarningsSource abstract base class and YAML config loader."""

import logging
import re
from abc import ABC, abstractmethod
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
import yaml

logger = logging.getLogger(__name__)

_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4}$")


def _next_weekday() -> date:
    """Return the next weekday (Mon–Fri) from today."""
    d = date.today() + timedelta(days=1)
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d += timedelta(days=1)
    return d


def load_config(caller_file: str) -> dict:
    """Load the YAML config file adjacent to *caller_file*.

    Looks for a file with the same stem and ``.yaml`` extension.
    E.g. ``sbi.py`` -> ``sbi.yaml``.

    Args:
        caller_file: ``__file__`` of the calling module.

    Returns:
        Parsed YAML as a dict.
    """
    yaml_path = Path(caller_file).with_suffix(".yaml")
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class EarningsSource(ABC):
    """Abstract base class for earnings calendar sources.

    Subclasses must implement ``name`` and ``_fetch``.
    The public ``fetch`` method wraps ``_fetch`` with validation.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short lowercase identifier, e.g. ``"sbi"``."""

    @abstractmethod
    def _fetch(self, date: str) -> pd.DataFrame:
        """Fetch raw earnings data for *date*.

        Must return a DataFrame with at least ``code`` and ``datetime`` columns.
        """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self, date: str) -> pd.DataFrame:
        """Fetch and validate earnings data for *date*.

        Validation:
        - ``code`` and ``datetime`` columns must exist.
        - ``code`` coerced to ``str`` and validated against ``^[0-9A-Z]{4}$``.
        - ``datetime`` coerced via ``pd.to_datetime(errors="coerce")``.
        - Invalid rows dropped with a warning.

        Returns:
            Validated DataFrame with ``[code, name, datetime]`` columns.
        """
        df = self._fetch(date)

        if df.empty:
            return df

        # Ensure required columns
        if "code" not in df.columns or "datetime" not in df.columns:
            logger.warning(f"[{self.name}] Missing required columns (code, datetime)")
            return pd.DataFrame(columns=["code", "name", "datetime"])

        # Coerce types
        df["code"] = df["code"].astype(str)
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

        # Validate code format
        valid_mask = df["code"].str.match(_CODE_PATTERN)
        n_invalid = (~valid_mask).sum()
        if n_invalid > 0:
            logger.warning(f"[{self.name}] Dropping {n_invalid} rows with invalid code")
            df = df[valid_mask]

        # Note: NaT datetimes are allowed (unknown time). Only drop if code is missing.

        return df.reset_index(drop=True)

    def check(self) -> dict:
        """Health check using test_date and min_rows from YAML config.

        Returns:
            Dict with ``name``, ``ok`` (bool), ``rows`` (int), and ``error`` (str|None).
        """
        result: dict = {"name": self.name, "ok": False, "rows": 0, "error": None}
        try:
            cfg = getattr(self, "_config", {})
            hc = cfg.get("health_check", {})
            test_date = hc.get("test_date") or _next_weekday().isoformat()
            min_rows = hc.get("min_rows", 1)

            df = self.fetch(test_date)
            result["rows"] = len(df)
            result["ok"] = len(df) >= min_rows
            if not result["ok"]:
                result["error"] = f"Expected >= {min_rows} rows, got {len(df)}"
        except (ValueError, RuntimeError, OSError, requests.RequestException) as e:
            result["error"] = str(e)

        return result
