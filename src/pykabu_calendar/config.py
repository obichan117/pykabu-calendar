"""
Shared configuration for all scrapers.

This file contains ONLY shared settings used across all sources.
Source-specific config lives in sources/{name}/config.py

Runtime configuration:
    import pykabu_calendar as cal
    cal.configure(llm_model="gemini-2.0-flash-lite", cache_ttl_days=7)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Settings:
    """Centralized configuration for pykabu-calendar.

    All values have sensible defaults. Override at runtime via ``configure()``.
    API keys are NOT stored here — pass them explicitly or use env vars.
    """

    # HTTP
    timeout: int = 30
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    # LLM
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.0-flash"
    llm_timeout: float = 60.0

    # Cache
    cache_dir: str = "~/.pykabu_calendar"
    cache_ttl_days: int = 30

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
_on_configure_hooks: list[Callable[[], None]] = []


def get_settings() -> Settings:
    """Get the current settings (creates defaults on first call)."""
    global _settings
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


# ---------------------------------------------------------------------------
# Module-level constants used by core/fetch.py, earnings/ir/, and tests.
# ---------------------------------------------------------------------------

# Modern Chrome User-Agent (update periodically)
USER_AGENT = Settings().user_agent

# Default request timeout in seconds
TIMEOUT = Settings().timeout

# Default request headers
HEADERS = Settings().headers
