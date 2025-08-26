"""Caching system for media scan results."""

from __future__ import annotations

import hashlib
import json
import pickle
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    data: Any
    file_path: Path
    file_size: int
    file_mtime: float
    cache_time: float


class MediaCache:
    """Cache for media scan results."""

    def __init__(self, cache_dir: Path | None = None, enabled: bool = True):
        """Initialize cache."""
        self.enabled = enabled
        if not enabled:
            return

        self.cache_dir = cache_dir or (Path.home() / ".cache" / "media-audit")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
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

    def _get_file_key(self, file_path: Path, prefix: str = "") -> str:
        """Generate cache key for file."""
        # Use path and prefix to create unique key
        key_str = f"{prefix}:{file_path.absolute()}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _is_cache_valid(self, entry: CacheEntry, file_path: Path) -> bool:
        """Check if cache entry is still valid."""
        if not file_path.exists():
            return False
        
        try:
            stat = file_path.stat()
            # Check if file has been modified
            if stat.st_mtime != entry.file_mtime or stat.st_size != entry.file_size:
                return False
            return True
        except (OSError, IOError):
            return False

    def get_probe_data(self, file_path: Path) -> dict[str, Any] | None:
        """Get cached ffprobe data for video file."""
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
                with open(cache_file, "rb") as f:
                    entry = pickle.load(f)
                if self._is_cache_valid(entry, file_path):
                    self._memory_cache[key] = entry
                    self.hits += 1
                    return entry.data  # type: ignore[no-any-return]
            except Exception:
                # Invalid cache entry, will be regenerated
                pass
        
        self.misses += 1
        return None

    def set_probe_data(self, file_path: Path, data: dict[str, Any]) -> None:
        """Cache ffprobe data for video file."""
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
            )
            
            # Save to memory cache
            self._memory_cache[key] = entry
            
            # Save to disk cache
            cache_file = self.probe_cache_dir / f"{key}.pkl"
            with open(cache_file, "wb") as f:
                pickle.dump(entry, f)
        except Exception:
            # Silently fail on cache write errors
            pass

    def get_media_item(self, directory: Path, item_type: str) -> dict[str, Any] | None:
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
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
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

    def set_media_item(self, directory: Path, item_type: str, data: dict[str, Any]) -> None:
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
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f)
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
                except (OSError, IOError):
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
            if dir_mtime > entry.file_mtime:
                return False
            return True
        except Exception:
            return False

    def clear(self) -> None:
        """Clear all cache."""
        if not self.enabled:
            return
            
        self._memory_cache.clear()
        
        # Clear disk cache
        for cache_file in self.probe_cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception:
                pass
                
        for cache_file in self.scan_cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except Exception:
                pass

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
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