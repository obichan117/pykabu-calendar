"""Tests for IR discovery cache module."""

import json
import pytest
from datetime import datetime, timedelta

from pykabu_calendar.earnings.ir import (
    CacheEntry,
    IRCache,
    IRPageType,
    get_cache,
    get_cached,
    save_cache,
)
from pykabu_calendar.config import get_settings


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_basic_creation(self):
        """Test creating a CacheEntry."""
        entry = CacheEntry(
            ir_url="https://example.com/ir/",
            ir_type=IRPageType.LANDING,
            last_updated="2025-01-15T10:00:00",
        )
        assert entry.ir_url == "https://example.com/ir/"
        assert entry.ir_type == IRPageType.LANDING
        assert entry.success_count == 1

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "ir_url": "https://example.com/ir/",
            "ir_type": "calendar",
            "last_updated": "2025-01-15T10:00:00",
            "discovered_via": "llm",
            "success_count": 5,
        }
        entry = CacheEntry.from_dict(data)
        assert entry.ir_url == data["ir_url"]
        assert entry.discovered_via == "llm"
        assert entry.success_count == 5

    def test_to_dict(self):
        """Test converting to dictionary."""
        entry = CacheEntry(
            ir_url="https://example.com/ir/",
            ir_type=IRPageType.LANDING,
            last_updated="2025-01-15T10:00:00",
        )
        data = entry.to_dict()
        assert data["ir_url"] == "https://example.com/ir/"
        assert data["ir_type"] == "landing"

    def test_is_expired_not_expired(self):
        """Test is_expired when entry is fresh."""
        entry = CacheEntry(
            ir_url="https://example.com/ir/",
            ir_type=IRPageType.LANDING,
            last_updated=datetime.now().isoformat(),
        )
        assert not entry.is_expired()

    def test_is_expired_when_expired(self):
        """Test is_expired when entry is old."""
        old_date = datetime.now() - timedelta(days=get_settings().cache_ttl_days + 1)
        entry = CacheEntry(
            ir_url="https://example.com/ir/",
            ir_type=IRPageType.LANDING,
            last_updated=old_date.isoformat(),
        )
        assert entry.is_expired()

    def test_is_expired_custom_ttl(self):
        """Test is_expired with custom TTL."""
        date = datetime.now() - timedelta(days=5)
        entry = CacheEntry(
            ir_url="https://example.com/ir/",
            ir_type=IRPageType.LANDING,
            last_updated=date.isoformat(),
        )
        assert not entry.is_expired(ttl_days=10)
        assert entry.is_expired(ttl_days=3)


class TestIRCache:
    """Tests for IRCache class."""

    @pytest.fixture
    def temp_cache(self, tmp_path):
        """Create a temporary cache for testing."""
        return IRCache(cache_dir=tmp_path, ttl_days=30)

    def test_cache_path(self, temp_cache, tmp_path):
        """Test cache path property."""
        assert temp_cache.cache_path == tmp_path / "ir_cache.json"

    def test_get_nonexistent(self, temp_cache):
        """Test getting nonexistent entry."""
        result = temp_cache.get("9999")
        assert result is None

    def test_set_and_get(self, temp_cache):
        """Test setting and getting an entry."""
        temp_cache.set(
            code="7203",
            ir_url="https://global.toyota/jp/ir/",
            ir_type=IRPageType.LANDING,
        )

        result = temp_cache.get("7203")
        assert result is not None
        assert result.ir_url == "https://global.toyota/jp/ir/"
        assert result.ir_type == IRPageType.LANDING

    def test_set_updates_existing(self, temp_cache):
        """Test that set updates existing entry."""
        temp_cache.set(
            code="7203",
            ir_url="https://global.toyota/jp/ir/",
            ir_type=IRPageType.LANDING,
        )

        # Set again with same URL
        temp_cache.set(
            code="7203",
            ir_url="https://global.toyota/jp/ir/",
            ir_type=IRPageType.LANDING,
        )

        result = temp_cache.get("7203")
        assert result.success_count == 2

    def test_set_replaces_different_url(self, temp_cache):
        """Test that set replaces entry with different URL."""
        temp_cache.set(
            code="7203",
            ir_url="https://global.toyota/jp/ir/",
            ir_type=IRPageType.LANDING,
        )

        temp_cache.set(
            code="7203",
            ir_url="https://global.toyota/jp/ir/calendar/",
            ir_type=IRPageType.CALENDAR,
        )

        result = temp_cache.get("7203")
        assert result.ir_url == "https://global.toyota/jp/ir/calendar/"
        assert result.success_count == 1  # Reset for new URL

    def test_delete(self, temp_cache):
        """Test deleting an entry."""
        temp_cache.set(
            code="7203",
            ir_url="https://example.com/ir/",
            ir_type=IRPageType.LANDING,
        )

        assert temp_cache.delete("7203") is True
        assert temp_cache.get("7203") is None
        assert temp_cache.delete("7203") is False

    def test_clear(self, temp_cache):
        """Test clearing all entries."""
        temp_cache.set("7203", "https://a.com/ir/", IRPageType.LANDING)
        temp_cache.set("6758", "https://b.com/ir/", IRPageType.LANDING)

        count = temp_cache.clear()
        assert count == 2
        assert temp_cache.get("7203") is None
        assert temp_cache.get("6758") is None

    def test_persistence(self, tmp_path):
        """Test that cache persists across instances."""
        # Create and populate cache
        cache1 = IRCache(cache_dir=tmp_path)
        cache1.set("7203", "https://example.com/ir/", IRPageType.LANDING)

        # Create new instance and verify data persists
        cache2 = IRCache(cache_dir=tmp_path)
        result = cache2.get("7203")
        assert result is not None
        assert result.ir_url == "https://example.com/ir/"

    def test_cache_file_format(self, temp_cache, tmp_path):
        """Test that cache file is human-readable JSON."""
        temp_cache.set("7203", "https://example.com/ir/", IRPageType.LANDING)

        with open(temp_cache.cache_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should be valid JSON
        data = json.loads(content)
        assert "version" in data
        assert "companies" in data
        assert "7203" in data["companies"]

        # Should be indented (human-readable)
        assert "\n" in content
        assert "  " in content

    def test_get_expired_with_ignore(self, temp_cache):
        """Test getting expired entry with ignore_expired flag."""
        old_date = datetime.now() - timedelta(days=get_settings().cache_ttl_days + 1)
        temp_cache._cache["7203"] = CacheEntry(
            ir_url="https://example.com/ir/",
            ir_type=IRPageType.LANDING,
            last_updated=old_date.isoformat(),
        )
        temp_cache._loaded = True

        # Normal get should return None
        assert temp_cache.get("7203") is None

        # With ignore_expired should return entry
        result = temp_cache.get("7203", ignore_expired=True)
        assert result is not None


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.fixture(autouse=True)
    def _reset_global_cache(self):
        """Reset global cache before and after each test."""
        import pykabu_calendar.earnings.ir.cache as cache_module
        cache_module._global_cache = None
        yield
        cache_module._global_cache = None

    def test_get_cache(self, tmp_path):
        """Test get_cache function."""
        cache = get_cache(cache_dir=tmp_path)
        assert isinstance(cache, IRCache)
        assert cache.cache_dir == tmp_path

    def test_save_and_get_cached(self, tmp_path):
        """Test save_cache and get_cached functions."""
        import pykabu_calendar.earnings.ir.cache as cache_module

        # Set up global cache to point at tmp_path
        cache_module._global_cache = IRCache(cache_dir=tmp_path)

        entry = save_cache(
            code="7203",
            ir_url="https://example.com/ir/",
            ir_type=IRPageType.LANDING,
        )
        assert entry.ir_url == "https://example.com/ir/"

        result = get_cached("7203")
        assert result is not None
        assert result.ir_url == "https://example.com/ir/"
