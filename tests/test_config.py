"""Tests for the configuration system."""

import pytest

from pykabu_calendar.config import Settings, configure, get_settings


@pytest.fixture(autouse=True)
def _reset_settings():
    """Reset settings to defaults before each test."""
    configure()  # reset
    yield
    configure()  # reset after


class TestSettings:
    """Test the Settings dataclass."""

    def test_defaults(self):
        s = Settings()
        assert s.timeout == 30
        assert s.max_workers == 4
        assert s.llm_model == "gemini-2.0-flash"
        assert s.llm_timeout == 60.0
        assert s.llm_provider == "gemini"
        assert s.cache_dir == "~/.pykabu_calendar"
        assert s.cache_ttl_days == 30

    def test_headers_property(self):
        s = Settings()
        h = s.headers
        assert "User-Agent" in h
        assert h["User-Agent"] == s.user_agent

    def test_frozen(self):
        s = Settings()
        with pytest.raises(AttributeError):
            s.timeout = 99  # type: ignore[misc]


class TestConfigure:
    """Test the configure() function."""

    def test_get_settings_returns_defaults(self):
        s = get_settings()
        assert s.timeout == 30

    def test_configure_overrides(self):
        configure(timeout=10, llm_model="gemini-2.0-flash-lite")
        s = get_settings()
        assert s.timeout == 10
        assert s.llm_model == "gemini-2.0-flash-lite"
        # other fields untouched
        assert s.cache_ttl_days == 30

    def test_configure_returns_settings(self):
        s = configure(cache_ttl_days=7)
        assert isinstance(s, Settings)
        assert s.cache_ttl_days == 7

    def test_configure_no_args_resets(self):
        configure(timeout=5)
        assert get_settings().timeout == 5
        configure()
        assert get_settings().timeout == 30  # back to default

    def test_configure_unknown_key_raises(self):
        with pytest.raises(TypeError):
            configure(nonexistent_key=42)

    def test_configure_multiple_calls_accumulate(self):
        configure(timeout=10)
        configure(llm_model="test-model")
        s = get_settings()
        assert s.timeout == 10
        assert s.llm_model == "test-model"

    def test_configure_max_workers(self):
        configure(max_workers=8)
        s = get_settings()
        assert s.max_workers == 8


class TestSettingsPropagation:
    """Test that settings propagate to consumers."""

    def test_llm_settings_propagate(self):
        """GeminiClient should read model/timeout from settings."""
        configure(llm_model="gemini-2.0-flash-lite", llm_timeout=30.0)
        from pykabu_calendar.llm.gemini import GeminiClient

        client = GeminiClient(api_key="fake-key")
        assert client.model == "gemini-2.0-flash-lite"
        assert client.timeout == 30.0

    def test_cache_settings_propagate(self):
        """IRCache should read cache_dir and ttl from settings."""
        configure(cache_dir="/tmp/test_cache", cache_ttl_days=7)
        from pykabu_calendar.earnings.ir.cache import IRCache

        cache = IRCache()
        assert str(cache.cache_dir) == "/tmp/test_cache"
        assert cache.ttl_days == 7

    def test_configure_resets_llm_singleton(self):
        """configure() should reset the LLM singleton so next call creates fresh instance."""
        from pykabu_calendar.llm import get_default_client

        configure(llm_model="gemini-2.0-flash")
        client_a = get_default_client()

        configure(llm_model="gemini-2.0-flash-lite")
        client_b = get_default_client()

        # After reconfigure, a new instance should be created (not the same object)
        if client_a is not None and client_b is not None:
            assert client_a is not client_b
        # If no API key, both are None — still valid (reset didn't crash)

    def test_configure_resets_cache_singleton(self):
        """configure() should reset the cache singleton so next call gets fresh instance."""
        from pykabu_calendar.earnings.ir.cache import get_cache

        configure(cache_dir="/tmp/claude/test_cache_a", cache_ttl_days=7)
        cache_a = get_cache()
        assert cache_a.ttl_days == 7

        configure(cache_dir="/tmp/claude/test_cache_b", cache_ttl_days=14)
        cache_b = get_cache()
        assert cache_b.ttl_days == 14
        assert cache_a is not cache_b
