"""Caching system for media scan results.

Provides persistent caching for ffprobe results and media scan data to improve
performance when re-scanning libraries. Implements both in-memory and disk-based
caching with automatic invalidation on file changes.

Key Features:
    - Separate caches for probe data and scan results
    - Automatic schema versioning and migration
    - File modification time tracking for invalidation
    - In-memory cache for current session
    - Cache statistics tracking

Example:
    >>> from media_audit.infrastructure.cache import MediaCache
    >>> cache = MediaCache(enabled=True)
    >>>
    >>> # Cache probe data
    >>> probe_data = expensive_ffprobe_operation(video_file)
    >>> cache.set_probe_data(video_file, probe_data)
    >>>
    >>> # Retrieve cached data
    >>> cached = cache.get_probe_data(video_file)
    >>> if cached:
    ...     print("Cache hit!")

"""

from __future__ import annotations

import contextlib
import hashlib
import json
import pickle
import time
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import aiofiles

from media_audit.shared.logging import get_logger

type T = Any

# Cache schema version - increment this when data structures change
# Or better, generate it from model definitions
CACHE_SCHEMA_VERSION = "2.0.0"


def generate_schema_hash() -> str:
    """Generate a hash of the current model schemas.

    Creates a unique hash based on the structure of all data models.
    Used to detect when models change and cache needs to be invalidated.

    Returns:
        str: 8-character hash of model schemas

    """
    from media_audit.core import (
        EpisodeItem,
        MediaAssets,
        MovieItem,
        SeasonItem,
        SeriesItem,
        ValidationIssue,
        VideoInfo,
    )

    # Collect field information from all models
    schema_info = []
    for model in [
        MovieItem,
        SeriesItem,
        SeasonItem,
        EpisodeItem,
        VideoInfo,
        MediaAssets,
        ValidationIssue,
    ]:
        model_fields = [f"{field.name}:{field.type}" for field in fields(model)]
        schema_info.append(f"{model.__name__}:{','.join(sorted(model_fields))}")

    # Generate hash of the schema
    schema_str = "|".join(sorted(schema_info))
    return hashlib.md5(schema_str.encode(), usedforsecurity=False).hexdigest()[:8]


@dataclass
class CacheEntry:
    """Cache entry with metadata for validation.

    Stores cached data along with file metadata to determine if the
    cache is still valid.

    Attributes:
        key: Unique cache key
        data: Cached data (any serializable type)
        file_path: Path to the original file
        file_size: Size of file when cached
        file_mtime: Modification time when cached
        cache_time: Timestamp when cached
        schema_version: Model schema version for compatibility

    """

    key: str
    data: Any
    file_path: Path
    file_size: int
    file_mtime: float
    cache_time: float
    schema_version: str | None = None  # Track schema version


class MediaCache:
    """Cache for media scan results and probe data.

    Manages persistent caching with automatic invalidation based on file
    changes and schema versions. Provides separate storage for different
    cache types and tracks hit/miss statistics.

    Attributes:
        enabled: Whether caching is active
        cache_dir: Root cache directory
        schema_version: Current model schema hash
        hits: Number of cache hits
        misses: Number of cache misses

    """

    def __init__(self, cache_dir: Path | None = None, enabled: bool = True):
        """Initialize cache system.

        Sets up cache directories and checks for schema changes that would
        require cache invalidation.

        Args:
            cache_dir: Custom cache directory (defaults to ~/.cache/media-audit)
            enabled: Whether to enable caching

        """
        self.enabled = enabled
        self.logger = get_logger("cache")
        if not enabled:
            return

        self.cache_dir = cache_dir or (Path.home() / ".cache" / "media-audit")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Generate current schema version
        self.schema_version = generate_schema_hash()

        # Check if schema has changed and clear old cache if needed
        self._check_and_migrate_cache()

        # Separate caches for different types
        self.probe_cache_dir = self.cache_dir / "probe"
        self.probe_cache_dir.mkdir(exist_ok=True)

        self.scan_cache_dir = self.cache_dir / "scan"
        self.scan_cache_dir.mkdir(exist_ok=True)

        # In-memory cache for current session
        self._memory_cache: dict[str, CacheEntry] = {}

        # Track cache statistics
        self.hits = 0
        self.misses = 0

    def _check_and_migrate_cache(self) -> None:
        """Check cache version and clear if schema has changed.

        Compares stored schema version with current version and clears
        the cache if they don't match, preventing deserialization errors.
        """
        version_file = self.cache_dir / "schema_version.txt"

        if version_file.exists():
            try:
                stored_version = version_file.read_text().strip()
                if stored_version != self.schema_version:
                    # Schema has changed, clear the cache
                    self.logger.warning("Cache schema changed, clearing old cache data...")
                    self.clear()
            except Exception as e:
                self.logger.debug(f"Failed to load cache version: {e}")

        # Write current version
        with contextlib.suppress(Exception):
            version_file.write_text(self.schema_version)

    def _get_file_key(self, file_path: Path, prefix: str = "") -> str:
        """Generate unique cache key for a file.

        Args:
            file_path: Path to file
            prefix: Optional prefix for key namespacing

        Returns:
            str: MD5 hash key for cache lookup

        """
        # Use path and prefix to create unique key
        key_str = f"{prefix}:{file_path.absolute()}"
        return hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()

    def _is_cache_valid(self, entry: CacheEntry, file_path: Path) -> bool:
        """Check if cache entry is still valid.

        Validates cache based on file existence, modification time,
        size, and schema version.

        Args:
            entry: Cache entry to validate
            file_path: Current file path

        Returns:
            bool: True if cache is still valid

        """
        if not file_path.exists():
            return False

        # Check schema version
        if hasattr(entry, "schema_version") and entry.schema_version != self.schema_version:
            return False

        try:
            stat = file_path.stat()
            # Check if file has been modified
            return stat.st_mtime == entry.file_mtime and stat.st_size == entry.file_size
        except OSError as e:
            self.logger.debug(f"Failed to stat file {file_path}: {e}")
            return False

    async def get_probe_data(self, file_path: Path) -> dict[str, Any] | None:
        """Get cached ffprobe data for video file.

        Checks memory cache first, then disk cache. Validates cache
        before returning.

        Args:
            file_path: Path to video file

        Returns:
            dict[str, Any] | None: Cached probe data or None if not found/invalid

        """
        if not self.enabled:
            return None

        key = self._get_file_key(file_path, "probe")

        # Check memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if self._is_cache_valid(entry, file_path):
                self.hits += 1
                return entry.data  # type: ignore[no-any-return]

        # Check disk cache
        cache_file = self.probe_cache_dir / f"{key}.pkl"
        if cache_file.exists():
            try:
                async with aiofiles.open(cache_file, "rb") as f:
                    content = await f.read()
                    entry = pickle.loads(content)  # nosec B301 - trusted cache files
                if self._is_cache_valid(entry, file_path):
                    self._memory_cache[key] = entry
                    self.hits += 1
                    return entry.data  # type: ignore[no-any-return]
            except Exception:
                # Invalid cache entry, will be regenerated
                pass

        self.misses += 1
        return None

    async def set_probe_data(self, file_path: Path, data: dict[str, Any]) -> None:
        """Cache ffprobe data for video file.

        Stores data in both memory and disk cache.

        Args:
            file_path: Path to video file
            data: Probe data to cache

        """
        if not self.enabled:
            return

        key = self._get_file_key(file_path, "probe")

        try:
            stat = file_path.stat()
            entry = CacheEntry(
                key=key,
                data=data,
                file_path=file_path,
                file_size=stat.st_size,
                file_mtime=stat.st_mtime,
                cache_time=time.time(),
                schema_version=self.schema_version,
            )

            # Save to memory cache
            self._memory_cache[key] = entry

            # Save to disk cache
            cache_file = self.probe_cache_dir / f"{key}.pkl"
            async with aiofiles.open(cache_file, "wb") as f:
                await f.write(pickle.dumps(entry))  # nosec B301 - trusted cache files
        except Exception:
            # Silently fail on cache write errors
            pass

    async def get_media_item(self, directory: Path, item_type: str) -> dict[str, Any] | None:
        """Get cached media item data."""
        if not self.enabled:
            return None

        key = self._get_file_key(directory, f"media:{item_type}")

        # Check memory cache
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if self._is_cache_valid_for_directory(entry, directory):
                self.hits += 1
                return entry.data  # type: ignore[no-any-return]

        # Check disk cache
        cache_file = self.scan_cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                async with aiofiles.open(cache_file, encoding="utf-8") as f:
                    content = await f.read()
                    cache_data = json.loads(content)
                    entry = CacheEntry(**cache_data)
                    entry.file_path = Path(entry.file_path)  # Convert string back to Path

                if self._is_cache_valid_for_directory(entry, directory):
                    self._memory_cache[key] = entry
                    self.hits += 1
                    return entry.data  # type: ignore[no-any-return]
            except Exception:
                pass

        self.misses += 1
        return None

    async def set_media_item(self, directory: Path, item_type: str, data: dict[str, Any]) -> None:
        """Cache media item data."""
        if not self.enabled:
            return

        key = self._get_file_key(directory, f"media:{item_type}")

        try:
            # Get directory modification time
            dir_mtime = self._get_directory_mtime(directory)

            entry = CacheEntry(
                key=key,
                data=data,
                file_path=directory,
                file_size=0,  # Not used for directories
                file_mtime=dir_mtime,
                cache_time=time.time(),
                schema_version=self.schema_version,
            )

            # Save to memory cache
            self._memory_cache[key] = entry

            # Save to disk cache (JSON for media items)
            cache_file = self.scan_cache_dir / f"{key}.json"
            cache_data = {
                "key": entry.key,
                "data": entry.data,
                "file_path": str(entry.file_path),
                "file_size": entry.file_size,
                "file_mtime": entry.file_mtime,
                "cache_time": entry.cache_time,
                "schema_version": entry.schema_version,
            }
            async with aiofiles.open(cache_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(cache_data))
        except Exception:
            pass

    def _get_directory_mtime(self, directory: Path) -> float:
        """Get most recent modification time in directory."""
        try:
            # Check directory itself
            max_mtime = directory.stat().st_mtime

            # Check immediate children (don't recurse deeply)
            for item in directory.iterdir():
                try:
                    item_mtime = item.stat().st_mtime
                    max_mtime = max(max_mtime, item_mtime)
                except OSError:
                    continue

            return max_mtime
        except Exception:
            return time.time()

    def _is_cache_valid_for_directory(self, entry: CacheEntry, directory: Path) -> bool:
        """Check if cache entry is valid for directory."""
        if not directory.exists():
            return False

        try:
            # Check if directory has been modified
            dir_mtime = self._get_directory_mtime(directory)

            # Directory has been modified if mtime is newer than cache time
            return dir_mtime <= entry.file_mtime
        except Exception:
            return False

    def clear(self) -> None:
        """Clear all cached data.

        Removes both memory and disk cache entries. Used when schema
        changes or for manual cache clearing.
        """
        if not self.enabled:
            return

        self._memory_cache.clear()

        # Clear disk cache
        for cache_file in self.probe_cache_dir.glob("*.pkl"):
            with contextlib.suppress(Exception):
                cache_file.unlink()

        for cache_file in self.scan_cache_dir.glob("*.json"):
            with contextlib.suppress(Exception):
                cache_file.unlink()

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            dict[str, Any]: Statistics including hits, misses, hit rate,
                          and cache file counts

        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate": hit_rate,
            "memory_entries": len(self._memory_cache),
            "probe_cache_files": len(list(self.probe_cache_dir.glob("*.pkl"))),
            "scan_cache_files": len(list(self.scan_cache_dir.glob("*.json"))),
        }
