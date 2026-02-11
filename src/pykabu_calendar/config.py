"""
Shared configuration for all scrapers.

This file contains ONLY shared settings used across all sources.
Source-specific config lives in sources/{name}/config.py

Runtime configuration:
    import pykabu_calendar as cal
    cal.configure(llm_model="gemini-2.0-flash-lite", cache_ttl_days=7)
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

import yaml


def _load_defaults() -> dict:
    """Load default values from config.yaml."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


_DEFAULTS = _load_defaults()


@dataclass(frozen=True)
class Settings:
    """Centralized configuration for pykabu-calendar.

    All values have sensible defaults. Override at runtime via ``configure()``.
    API keys are NOT stored here — pass them explicitly or use env vars.
    """

    # HTTP
    timeout: int = _DEFAULTS["timeout"]
    user_agent: str = _DEFAULTS["user_agent"]

    # Parallelism
    max_workers: int = _DEFAULTS["max_workers"]

    # LLM
    llm_provider: str = _DEFAULTS["llm_provider"]
    llm_model: str = _DEFAULTS["llm_model"]
    llm_timeout: float = _DEFAULTS["llm_timeout"]
    llm_temperature: float = _DEFAULTS["llm_temperature"]
    llm_max_output_tokens: int = _DEFAULTS["llm_max_output_tokens"]
    llm_rate_limit_rpm: int = _DEFAULTS["llm_rate_limit_rpm"]
    llm_find_link_max_chars: int = _DEFAULTS["llm_find_link_max_chars"]
    llm_extract_datetime_max_chars: int = _DEFAULTS["llm_extract_datetime_max_chars"]

    # Cache
    cache_dir: str = _DEFAULTS["cache_dir"]
    cache_ttl_days: int = _DEFAULTS["cache_ttl_days"]

    @property
    def headers(self) -> dict[str, str]:
        """HTTP request headers derived from settings."""
        return {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }


# Module-level singleton
_settings: Settings | None = None
_settings_lock = threading.Lock()
_on_configure_hooks: list[Callable[[], None]] = []


def get_settings() -> Settings:
    """Get the current settings (creates defaults on first call)."""
    global _settings
    if _settings is not None:
        return _settings
    with _settings_lock:
        if _settings is None:
            _settings = Settings()
        return _settings


def configure(**kwargs) -> Settings:
    """Override configuration at runtime.

    Unknown keys raise ``TypeError``. Call with no args to reset to defaults.

    Example::

        from pykabu_calendar.config import configure
        configure(llm_model="gemini-2.0-flash-lite", cache_ttl_days=7)

    Returns:
        The new Settings instance.
    """
    global _settings
    with _settings_lock:
        if not kwargs:
            _settings = Settings()
        else:
            _settings = replace(get_settings(), **kwargs)
    # Notify subscribers (LLM singleton, cache singleton, etc.)
    for hook in _on_configure_hooks:
        hook()
    return _settings


def on_configure(hook: Callable[[], None]) -> None:
    """Register a callback invoked whenever ``configure()`` is called.

    Used internally so that singletons (LLM client, cache) can reset
    themselves when settings change.  Not part of the public API.
    """
    _on_configure_hooks.append(hook)
