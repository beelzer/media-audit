"""Tests for caching functionality."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from media_audit.infrastructure.cache import MediaCache


@pytest.fixture
def cache(tmp_path):
    """Create a cache instance."""
    return MediaCache(cache_dir=tmp_path / "cache", enabled=True)


@pytest.fixture
def disabled_cache(tmp_path):
    """Create a disabled cache instance."""
    return MediaCache(cache_dir=tmp_path / "cache", enabled=False)


def test_cache_initialization(cache):
    """Test cache initialization."""
    assert cache.enabled
    assert cache.cache_dir.exists()
    assert cache.probe_cache_dir.exists()
    assert cache.scan_cache_dir.exists()
    assert cache.hits == 0
    assert cache.misses == 0


@pytest.mark.asyncio
async def test_disabled_cache(disabled_cache):
    """Test disabled cache."""
    assert not disabled_cache.enabled

    # Operations should be no-ops
    test_file = Path("/test/video.mp4")
    await disabled_cache.set_probe_data(test_file, {"test": "data"})
    assert await disabled_cache.get_probe_data(test_file) is None


@pytest.mark.asyncio
async def test_probe_cache(cache, tmp_path):
    """Test probe data caching."""
    # Create a test file
    test_file = tmp_path / "test.mp4"
    test_file.write_text("test content")

    # Initially no cached data
    assert await cache.get_probe_data(test_file) is None
    assert cache.misses == 1

    # Cache some data
    probe_data = {"codec": "h264", "duration": 120}
    await cache.set_probe_data(test_file, probe_data)

    # Retrieve cached data
    cached = await cache.get_probe_data(test_file)
    assert cached == probe_data
    assert cache.hits == 1

    # Check hit rate
    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 50.0


@pytest.mark.asyncio
async def test_cache_invalidation_on_file_change(cache, tmp_path):
    """Test cache invalidation when file changes."""
    test_file = tmp_path / "test.mp4"
    test_file.write_text("original content")

    # Cache data
    await cache.set_probe_data(test_file, {"version": 1})
    assert await cache.get_probe_data(test_file) == {"version": 1}

    # Modify file (change mtime)
    time.sleep(0.01)  # Ensure different mtime
    test_file.write_text("modified content")

    # Cache should be invalidated
    assert await cache.get_probe_data(test_file) is None


@pytest.mark.asyncio
async def test_media_item_cache(cache, tmp_path):
    """Test media item caching."""
    test_dir = tmp_path / "Movie (2023)"
    test_dir.mkdir()

    # Cache media item
    item_data = {
        "name": "Movie",
        "year": 2023,
        "type": "movie",
    }

    await cache.set_media_item(test_dir, "movie", item_data)

    # Retrieve cached item
    cached = await cache.get_media_item(test_dir, "movie")
    assert cached == item_data


@pytest.mark.asyncio
async def test_directory_cache_invalidation(cache, tmp_path):
    """Test cache invalidation for directories."""
    test_dir = tmp_path / "Series"
    test_dir.mkdir()

    # Cache data
    await cache.set_media_item(test_dir, "tv", {"name": "Series"})
    assert await cache.get_media_item(test_dir, "tv") == {"name": "Series"}

    # Add a file to directory with sufficient time delay
    time.sleep(0.1)  # Increase delay for Windows filesystem precision
    (test_dir / "new_file.txt").write_text("new")

    # Cache should be invalidated
    assert await cache.get_media_item(test_dir, "tv") is None


@pytest.mark.asyncio
async def test_cache_persistence(tmp_path):
    """Test cache persists across instances."""
    cache_dir = tmp_path / "persistent_cache"
    test_file = tmp_path / "video.mp4"
    test_file.write_text("content")

    # First cache instance
    cache1 = MediaCache(cache_dir=cache_dir)
    await cache1.set_probe_data(test_file, {"persistent": True})

    # New cache instance with same directory
    cache2 = MediaCache(cache_dir=cache_dir)
    assert await cache2.get_probe_data(test_file) == {"persistent": True}


@pytest.mark.asyncio
async def test_cache_clear(cache, tmp_path):
    """Test clearing cache."""
    test_file = tmp_path / "test.mp4"
    test_file.write_text("content")

    # Add data to cache
    await cache.set_probe_data(test_file, {"data": "test"})
    assert await cache.get_probe_data(test_file) is not None

    # Clear cache
    cache.clear()
    assert len(cache._memory_cache) == 0
    assert await cache.get_probe_data(test_file) is None
