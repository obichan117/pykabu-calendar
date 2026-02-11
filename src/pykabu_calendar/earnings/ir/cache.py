"""JSON cache for IR discovery results."""

import dataclasses
import json
import logging
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ...config import get_settings, on_configure
from .discovery import IRPageType

logger = logging.getLogger(__name__)

DEFAULT_CACHE_FILE = "ir_cache.json"


@dataclass
class CacheEntry:
    """Cache entry for a company's IR page discovery."""

    ir_url: str
    ir_type: IRPageType
    last_updated: str  # ISO format datetime
    discovered_via: str = "pattern"  # "pattern", "llm", "homepage_link", "manual"
    parse_pattern: str | None = None  # Successful parsing pattern (if rule-based)
    success_count: int = 1  # How many times parsing succeeded
    last_earnings_datetime: str | None = None  # Last successfully parsed datetime

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheEntry":
        """Create CacheEntry from dictionary."""
        fields = {f.name for f in dataclasses.fields(cls)}
        known = {k: v for k, v in data.items() if k in fields}
        # Deserialize ir_type string to enum
        ir_type_raw = known.pop("ir_type", "unknown")
        try:
            known["ir_type"] = IRPageType(ir_type_raw)
        except ValueError:
            known["ir_type"] = IRPageType.UNKNOWN
        return cls(**known)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d["ir_type"] = self.ir_type.value
        return d

    def is_expired(self, ttl_days: int | None = None) -> bool:
        """Check if this cache entry has expired.

        Args:
            ttl_days: Time-to-live in days (default: from settings)

        Returns:
            True if expired, False otherwise
        """
        if ttl_days is None:
            ttl_days = get_settings().cache_ttl_days
        try:
            updated = datetime.fromisoformat(self.last_updated)
            expiry = updated + timedelta(days=ttl_days)
            return datetime.now() > expiry
        except ValueError:
            return True  # Invalid timestamp = expired


class IRCache:
    """Cache manager for IR discovery results.

    Stores discovered IR page URLs and parsing patterns in a JSON file.
    Supports manual editing and sharing of cache files.
    """

    def __init__(
        self,
        cache_dir: Path | str | None = None,
        cache_file: str = DEFAULT_CACHE_FILE,
        ttl_days: int | None = None,
    ):
        """Initialize cache manager.

        Args:
            cache_dir: Directory to store cache file (default: from settings)
            cache_file: Cache filename (default: ir_cache.json)
            ttl_days: Cache entry TTL in days (default: from settings)
        """
        settings = get_settings()
        self.cache_dir = Path(cache_dir) if cache_dir else Path(settings.cache_dir).expanduser()
        self.cache_file = cache_file
        self.ttl_days = ttl_days if ttl_days is not None else settings.cache_ttl_days
        self._cache: dict[str, CacheEntry] = {}
        self._loaded = False
        self._lock = threading.Lock()

    @property
    def cache_path(self) -> Path:
        """Full path to the cache file."""
        return self.cache_dir / self.cache_file

    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """Load cache from disk."""
        if self._loaded:
            return

        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for code, entry_data in data.get("companies", {}).items():
                    try:
                        self._cache[code] = CacheEntry.from_dict(entry_data)
                    except (KeyError, TypeError) as e:
                        logger.warning(f"Invalid cache entry for {code}: {e}")

                logger.debug(f"Loaded {len(self._cache)} entries from cache")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load cache: {e}")

        self._loaded = True

    def _save(self) -> None:
        """Save cache to disk."""
        self._ensure_cache_dir()

        data = {
            "version": "1.0",
            "updated": datetime.now().isoformat(),
            "companies": {code: entry.to_dict() for code, entry in self._cache.items()},
        }

        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(self._cache)} entries to cache")
        except IOError as e:
            logger.warning(f"Failed to save cache: {e}")

    def get(self, code: str, ignore_expired: bool = False) -> CacheEntry | None:
        """Get cached entry for a company.

        Args:
            code: Stock code
            ignore_expired: If True, return entry even if expired

        Returns:
            CacheEntry if found and valid, None otherwise
        """
        with self._lock:
            self._load()

            entry = self._cache.get(code)
            if entry is None:
                return None

            if not ignore_expired and entry.is_expired(self.ttl_days):
                logger.debug(f"Cache entry for {code} has expired")
                return None

            return entry

    def set(
        self,
        code: str,
        ir_url: str,
        ir_type: IRPageType | str,
        discovered_via: str = "pattern",
        parse_pattern: str | None = None,
        last_earnings_datetime: datetime | None = None,
    ) -> CacheEntry:
        """Set or update cache entry for a company.

        Args:
            code: Stock code
            ir_url: Discovered IR page URL
            ir_type: Type of IR page
            discovered_via: How the page was discovered
            parse_pattern: Successful parsing pattern (if any)
            last_earnings_datetime: Last successfully parsed datetime

        Returns:
            The created/updated CacheEntry
        """
        with self._lock:
            self._load()

            # Normalize ir_type to enum
            if isinstance(ir_type, str):
                try:
                    ir_type = IRPageType(ir_type)
                except ValueError:
                    ir_type = IRPageType.UNKNOWN

            # Update existing entry or create new one
            existing = self._cache.get(code)
            if existing and existing.ir_url == ir_url:
                # Update existing entry
                existing.last_updated = datetime.now().isoformat()
                existing.success_count += 1
                if parse_pattern:
                    existing.parse_pattern = parse_pattern
                if last_earnings_datetime:
                    existing.last_earnings_datetime = last_earnings_datetime.isoformat()
                entry = existing
            else:
                # Create new entry
                entry = CacheEntry(
                    ir_url=ir_url,
                    ir_type=ir_type,
                    last_updated=datetime.now().isoformat(),
                    discovered_via=discovered_via,
                    parse_pattern=parse_pattern,
                    success_count=1,
                    last_earnings_datetime=(
                        last_earnings_datetime.isoformat() if last_earnings_datetime else None
                    ),
                )
                self._cache[code] = entry

            self._save()
            return entry

    def delete(self, code: str) -> bool:
        """Delete cache entry for a company.

        Args:
            code: Stock code

        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            self._load()

            if code in self._cache:
                del self._cache[code]
                self._save()
                return True
            return False

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            self._load()
            count = len(self._cache)
            self._cache.clear()
            self._save()
            return count



# Global cache instance (lazy initialization, thread-safe)
_global_cache: IRCache | None = None
_global_cache_lock = threading.Lock()


def get_cache(
    cache_dir: Path | str | None = None,
    ttl_days: int | None = None,
) -> IRCache:
    """Get the global cache instance.

    Args:
        cache_dir: Optional custom cache directory (default: from settings)
        ttl_days: Cache TTL in days (default: from settings)

    Returns:
        IRCache instance
    """
    global _global_cache

    with _global_cache_lock:
        if _global_cache is None or cache_dir is not None:
            _global_cache = IRCache(cache_dir=cache_dir, ttl_days=ttl_days)

    return _global_cache


def get_cached(code: str, ignore_expired: bool = False) -> CacheEntry | None:
    """Convenience function to get cached entry.

    Args:
        code: Stock code
        ignore_expired: If True, return entry even if expired

    Returns:
        CacheEntry if found and valid, None otherwise
    """
    return get_cache().get(code, ignore_expired=ignore_expired)


def save_cache(
    code: str,
    ir_url: str,
    ir_type: IRPageType | str,
    discovered_via: str = "pattern",
    parse_pattern: str | None = None,
    last_earnings_datetime: datetime | None = None,
) -> CacheEntry:
    """Convenience function to save cache entry.

    Args:
        code: Stock code
        ir_url: Discovered IR page URL
        ir_type: Type of IR page
        discovered_via: How the page was discovered
        parse_pattern: Successful parsing pattern (if any)
        last_earnings_datetime: Last successfully parsed datetime

    Returns:
        The created/updated CacheEntry
    """
    return get_cache().set(
        code=code,
        ir_url=ir_url,
        ir_type=ir_type,
        discovered_via=discovered_via,
        parse_pattern=parse_pattern,
        last_earnings_datetime=last_earnings_datetime,
    )


def _reset_global_cache() -> None:
    """Reset global cache so it picks up new settings on next access."""
    global _global_cache
    with _global_cache_lock:
        _global_cache = None


on_configure(_reset_global_cache)
