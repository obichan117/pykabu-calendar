"""JSON cache for IR discovery results."""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .discovery import IRPageType

logger = logging.getLogger(__name__)

# Default cache location
DEFAULT_CACHE_DIR = Path.home() / ".pykabu_calendar"
DEFAULT_CACHE_FILE = "ir_cache.json"
DEFAULT_TTL_DAYS = 30


@dataclass
class CacheEntry:
    """Cache entry for a company's IR page discovery."""

    ir_url: str
    ir_type: str  # IRPageType value as string
    last_updated: str  # ISO format datetime
    discovered_via: str = "pattern"  # "pattern", "llm", "homepage_link", "manual"
    parse_pattern: str | None = None  # Successful parsing pattern (if rule-based)
    success_count: int = 1  # How many times parsing succeeded
    last_earnings_datetime: str | None = None  # Last successfully parsed datetime

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheEntry":
        """Create CacheEntry from dictionary."""
        return cls(
            ir_url=data["ir_url"],
            ir_type=data.get("ir_type", "unknown"),
            last_updated=data["last_updated"],
            discovered_via=data.get("discovered_via", "pattern"),
            parse_pattern=data.get("parse_pattern"),
            success_count=data.get("success_count", 1),
            last_earnings_datetime=data.get("last_earnings_datetime"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def is_expired(self, ttl_days: int = DEFAULT_TTL_DAYS) -> bool:
        """Check if this cache entry has expired.

        Args:
            ttl_days: Time-to-live in days

        Returns:
            True if expired, False otherwise
        """
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
        ttl_days: int = DEFAULT_TTL_DAYS,
    ):
        """Initialize cache manager.

        Args:
            cache_dir: Directory to store cache file (default: ~/.pykabu_calendar/)
            cache_file: Cache filename (default: ir_cache.json)
            ttl_days: Cache entry TTL in days (default: 30)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.cache_file = cache_file
        self.ttl_days = ttl_days
        self._cache: dict[str, CacheEntry] = {}
        self._loaded = False

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
        self._load()

        # Convert IRPageType enum to string
        type_str = ir_type.value if isinstance(ir_type, IRPageType) else str(ir_type)

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
                ir_type=type_str,
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
        self._load()
        count = len(self._cache)
        self._cache.clear()
        self._save()
        return count

    def clear_expired(self) -> int:
        """Clear only expired cache entries.

        Returns:
            Number of entries cleared
        """
        self._load()

        expired_codes = [
            code
            for code, entry in self._cache.items()
            if entry.is_expired(self.ttl_days)
        ]

        for code in expired_codes:
            del self._cache[code]

        if expired_codes:
            self._save()

        return len(expired_codes)

    def list_all(self) -> dict[str, CacheEntry]:
        """List all cache entries.

        Returns:
            Dictionary of code -> CacheEntry
        """
        self._load()
        return dict(self._cache)

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        self._load()

        total = len(self._cache)
        expired = sum(
            1 for entry in self._cache.values() if entry.is_expired(self.ttl_days)
        )
        by_type = {}
        by_via = {}

        for entry in self._cache.values():
            by_type[entry.ir_type] = by_type.get(entry.ir_type, 0) + 1
            by_via[entry.discovered_via] = by_via.get(entry.discovered_via, 0) + 1

        return {
            "total": total,
            "expired": expired,
            "valid": total - expired,
            "by_type": by_type,
            "by_discovery_method": by_via,
            "cache_path": str(self.cache_path),
        }


# Global cache instance (lazy initialization)
_global_cache: IRCache | None = None


def get_cache(
    cache_dir: Path | str | None = None,
    ttl_days: int = DEFAULT_TTL_DAYS,
) -> IRCache:
    """Get the global cache instance.

    Args:
        cache_dir: Optional custom cache directory
        ttl_days: Cache TTL in days

    Returns:
        IRCache instance
    """
    global _global_cache

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
