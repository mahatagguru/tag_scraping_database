#!/usr/bin/env python3
"""
Caching system for intermediate scraping results with timestamp/checksum comparison.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any

import aiofiles


class CacheManager:
    """Manages caching of intermediate scraping results.

    Uses JSON-serialized file-based caching with an in-memory LRU-style layer.
    # TODO: implement database-backed cache layer if needed
    """

    def __init__(
        self,
        cache_dir: str = "cache",
        default_ttl: int = 3600,  # 1 hour
        enable_checksums: bool = True,
        max_memory_entries: int = 500,
    ):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for file-based cache
            default_ttl: Default time-to-live in seconds
            enable_checksums: Enable content checksum validation
            max_memory_entries: Maximum entries kept in the in-memory cache (FIFO eviction)
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.enable_checksums = enable_checksums
        self.max_memory_entries = max_memory_entries

        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

        # In-memory cache for frequently accessed data (bounded)
        self._memory_cache: dict[str, tuple[Any, float]] = {}

    def _get_cache_key(self, key: str, category: str = "default") -> str:
        """Generate cache key."""
        return f"{category}:{key}"

    def _get_file_path(self, key: str) -> str:
        """Get file path for cache entry."""
        # Use hash to avoid filesystem issues with special characters
        key_hash = hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.json.cache")

    def _calculate_checksum(self, data: Any) -> str:
        """Calculate checksum for data."""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        return hashlib.md5(data_str.encode(), usedforsecurity=False).hexdigest()

    def _is_cache_valid(self, timestamp: float, ttl: int) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - timestamp < ttl

    async def get(
        self, key: str, category: str = "default", ttl: int | None = None
    ) -> Any | None:
        """
        Get cached data.

        Args:
            key: Cache key
            category: Cache category
            ttl: Custom TTL override

        Returns:
            Cached data or None if not found/expired
        """
        cache_key = self._get_cache_key(key, category)
        ttl = ttl or self.default_ttl

        # Check memory cache first
        if cache_key in self._memory_cache:
            data, timestamp = self._memory_cache[cache_key]
            if self._is_cache_valid(timestamp, ttl):
                return data
            else:
                del self._memory_cache[cache_key]

        # Check file cache
        file_path = self._get_file_path(cache_key)
        if os.path.exists(file_path):
            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    cache_entry = json.loads(await f.read())

                data = cache_entry["data"]
                timestamp = cache_entry["timestamp"]

                if self._is_cache_valid(timestamp, ttl):
                    # Store in memory cache for faster access
                    self._memory_cache[cache_key] = (data, timestamp)
                    if len(self._memory_cache) > self.max_memory_entries:
                        oldest_key = next(iter(self._memory_cache))
                        del self._memory_cache[oldest_key]
                    return data
                else:
                    # Remove expired cache file
                    os.remove(file_path)

            except Exception as e:
                print(f"Error reading cache file {file_path}: {e}")

        return None

    async def set(
        self, key: str, data: Any, category: str = "default", ttl: int | None = None
    ) -> None:
        """
        Set cached data.

        Args:
            key: Cache key
            data: Data to cache
            category: Cache category
            ttl: Custom TTL override
        """
        cache_key = self._get_cache_key(key, category)
        timestamp = time.time()
        checksum = self._calculate_checksum(data) if self.enable_checksums else None

        # Store in memory cache (bounded FIFO)
        self._memory_cache[cache_key] = (data, timestamp)
        if len(self._memory_cache) > self.max_memory_entries:
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]

        # Store in file cache (JSON)
        try:
            file_path = self._get_file_path(cache_key)
            cache_entry = {
                "category": category,
                "data": data,
                "timestamp": timestamp,
                "checksum": checksum,
            }

            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(cache_entry))

        except Exception as e:
            print(f"Error writing cache file: {e}")

    async def invalidate(self, key: str, category: str = "default") -> None:
        """Invalidate cache entry."""
        cache_key = self._get_cache_key(key, category)

        # Remove from memory cache
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]

        # Remove file cache
        file_path = self._get_file_path(cache_key)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error removing cache file {file_path}: {e}")

    async def clear_category(self, category: str) -> None:
        """Clear all cache entries for a category."""
        # Clear memory cache
        keys_to_remove = [k for k in self._memory_cache if k.startswith(f"{category}:")]
        for key in keys_to_remove:
            del self._memory_cache[key]

        # Clear file cache — only remove files that belong to the target category
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith(".json.cache"):
                continue
            file_path = os.path.join(self.cache_dir, filename)
            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    cache_entry = json.loads(await f.read())
                if cache_entry.get("category") == category:
                    os.remove(file_path)
            except Exception:
                continue

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        memory_entries = len(self._memory_cache)
        file_entries = len(
            [f for f in os.listdir(self.cache_dir) if f.endswith(".json.cache")]
        )

        return {
            "memory_entries": memory_entries,
            "max_memory_entries": self.max_memory_entries,
            "file_entries": file_entries,
            "cache_directory": self.cache_dir,
        }


class ScrapingCacheManager:
    """Specialized cache manager for scraping operations."""

    def __init__(self, base_cache_manager: CacheManager):
        """Initialize scraping cache manager."""
        self.cache = base_cache_manager

        # Cache categories
        self.CATEGORIES = "categories"
        self.YEARS = "years"
        self.SETS = "sets"
        self.CARDS = "cards"
        self.CARD_DETAILS = "card_details"

        # TTL settings (in seconds)
        self.ttl_settings = {
            self.CATEGORIES: 24 * 3600,  # 24 hours
            self.YEARS: 12 * 3600,  # 12 hours
            self.SETS: 6 * 3600,  # 6 hours
            self.CARDS: 2 * 3600,  # 2 hours
            self.CARD_DETAILS: 3600,  # 1 hour
        }

    async def get_categories(self, sport: str) -> list[dict[str, Any]]:
        """Get cached categories for sport."""
        return await self.cache.get(f"categories_{sport}", self.CATEGORIES)

    async def set_categories(
        self, sport: str, categories: list[dict[str, Any]]
    ) -> None:
        """Cache categories for sport."""
        await self.cache.set(
            f"categories_{sport}",
            categories,
            self.CATEGORIES,
            self.ttl_settings[self.CATEGORIES],
        )

    async def get_years(self, sport: str) -> list[dict[str, Any]]:
        """Get cached years for sport."""
        return await self.cache.get(f"years_{sport}", self.YEARS)

    async def set_years(self, sport: str, years: list[dict[str, Any]]) -> None:
        """Cache years for sport."""
        await self.cache.set(
            f"years_{sport}", years, self.YEARS, self.ttl_settings[self.YEARS]
        )

    async def get_sets(self, sport: str, year: str) -> list[dict[str, Any]]:
        """Get cached sets for sport/year."""
        return await self.cache.get(f"sets_{sport}_{year}", self.SETS)

    async def set_sets(self, sport: str, year: str, sets: list[dict[str, Any]]) -> None:
        """Cache sets for sport/year."""
        await self.cache.set(
            f"sets_{sport}_{year}", sets, self.SETS, self.ttl_settings[self.SETS]
        )

    async def get_cards(
        self, sport: str, year: str, set_name: str
    ) -> list[dict[str, Any]]:
        """Get cached cards for sport/year/set."""
        return await self.cache.get(f"cards_{sport}_{year}_{set_name}", self.CARDS)

    async def set_cards(
        self, sport: str, year: str, set_name: str, cards: list[dict[str, Any]]
    ) -> None:
        """Cache cards for sport/year/set."""
        await self.cache.set(
            f"cards_{sport}_{year}_{set_name}",
            cards,
            self.CARDS,
            self.ttl_settings[self.CARDS],
        )

    async def get_card_details(self, card_url: str) -> dict[str, Any] | None:
        """Get cached card details."""
        return await self.cache.get(
            f"card_details_{hashlib.md5(card_url.encode(), usedforsecurity=False).hexdigest()}",
            self.CARD_DETAILS,
        )

    async def set_card_details(self, card_url: str, details: dict[str, Any]) -> None:
        """Cache card details."""
        await self.cache.set(
            f"card_details_{hashlib.md5(card_url.encode(), usedforsecurity=False).hexdigest()}",
            details,
            self.CARD_DETAILS,
            self.ttl_settings[self.CARD_DETAILS],
        )

    async def invalidate_sport_data(self, sport: str) -> None:
        """Invalidate all cached data for a sport."""
        await self.cache.invalidate(f"categories_{sport}", self.CATEGORIES)
        await self.cache.invalidate(f"years_{sport}", self.YEARS)

        # Note: For sets and cards, we'd need to enumerate all cached keys
        # This is a simplified implementation

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return await self.cache.get_stats()


# Global cache manager instance
_cache_manager: CacheManager | None = None
_scraping_cache: ScrapingCacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_scraping_cache() -> ScrapingCacheManager:
    """Get global scraping cache manager instance."""
    global _scraping_cache
    if _scraping_cache is None:
        _scraping_cache = ScrapingCacheManager(get_cache_manager())
    return _scraping_cache
