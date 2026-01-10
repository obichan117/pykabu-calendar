"""
Configuration for pykabu-calendar.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Global configuration for pykabu-calendar."""

    # LLM settings (for IR discovery)
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2"

    # Timeout settings
    timeout: int = 30  # seconds per request
    ir_timeout: int = 30  # seconds per company for IR discovery

    # Parallel processing
    parallel_workers: int = 5

    # Cache settings
    cache_path: Optional[Path] = None

    def __post_init__(self):
        if self.cache_path is None:
            self.cache_path = Path.home() / ".pykabu_calendar"


# Global config instance
_config = Config()


def configure(
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
    timeout: Optional[int] = None,
    ir_timeout: Optional[int] = None,
    parallel_workers: Optional[int] = None,
    cache_path: Optional[str] = None,
) -> None:
    """
    Configure global settings for pykabu-calendar.

    Args:
        llm_provider: LLM provider for IR discovery ("ollama", "anthropic", etc.)
        llm_model: Model name (e.g., "llama3.2", "gpt-4")
        timeout: Request timeout in seconds
        ir_timeout: IR discovery timeout per company
        parallel_workers: Number of concurrent workers for IR verification
        cache_path: Path to cache directory
    """
    global _config

    if llm_provider is not None:
        _config.llm_provider = llm_provider
    if llm_model is not None:
        _config.llm_model = llm_model
    if timeout is not None:
        _config.timeout = timeout
    if ir_timeout is not None:
        _config.ir_timeout = ir_timeout
    if parallel_workers is not None:
        _config.parallel_workers = parallel_workers
    if cache_path is not None:
        _config.cache_path = Path(cache_path)


def get_config() -> Config:
    """Get the current configuration."""
    return _config
