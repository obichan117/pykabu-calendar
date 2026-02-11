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
        """configure() should reset the LLM singleton."""
        import pykabu_calendar.llm as llm_mod

        llm_mod._default_client = "sentinel"  # type: ignore[assignment]
        configure(llm_model="new-model")
        assert llm_mod._default_client is None

    def test_configure_resets_cache_singleton(self):
        """configure() should reset the cache singleton."""
        import pykabu_calendar.earnings.ir.cache as cache_mod

        cache_mod._global_cache = "sentinel"  # type: ignore[assignment]
        configure(cache_ttl_days=1)
        assert cache_mod._global_cache is None
