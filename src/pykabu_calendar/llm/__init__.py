"""LLM providers for IR discovery and parsing."""

import logging

from ..config import on_configure
from .base import LLMClient, LLMResponse
from .gemini import GeminiClient

__all__ = ["LLMClient", "LLMResponse", "GeminiClient", "get_default_client", "reset_default_client"]

logger = logging.getLogger(__name__)

_default_client: LLMClient | None = None


def get_default_client() -> LLMClient | None:
    """Get the default LLM client (lazy singleton).

    Returns GeminiClient if API key is available, None otherwise.
    Settings (model, timeout) are read from ``get_settings()`` via GeminiClient.
    """
    global _default_client
    if _default_client is None:
        try:
            _default_client = GeminiClient()
        except ValueError:
            logger.debug("No LLM API key available")
            return None
    return _default_client


def reset_default_client() -> None:
    """Reset the default client so it picks up new settings on next access."""
    global _default_client
    _default_client = None


# Auto-reset when settings change
on_configure(reset_default_client)
