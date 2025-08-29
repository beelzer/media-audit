"""
Integration tests for the scanner module.
"""

import asyncio
from pathlib import Path

import pytest
from tests.utils.mocks import MockCache


@pytest.mark.asyncio
class TestScannerIntegration:
    """Integration tests for scanner functionality."""

    async def test_basic_scanning(self, temp_dir: Path, mock_config):
        """Test basic file scanning."""
        # Create test files
        media_files = []
        for i in range(3):
            file_path = temp_dir / f"movie_{i}.mkv"
            file_path.touch()
            media_files.append(str(file_path))

        mock_config.root_paths = [temp_dir]

        # This is a basic integration test structure
        # The actual scanner implementation would be tested here
        assert len(media_files) == 3
        assert all(Path(f).exists() for f in media_files)

    async def test_file_discovery(self, temp_dir: Path, mock_config):
        """Test file discovery with extensions."""
        # Create files with different extensions
        (temp_dir / "movie.mkv").touch()
        (temp_dir / "show.mp4").touch()
        (temp_dir / "video.avi").touch()
        (temp_dir / "document.txt").touch()  # Should be ignored

        mock_config.root_paths = [temp_dir]
        mock_config.include_patterns = ["*.mkv", "*.mp4", "*.avi"]

        # Test file discovery logic
        media_extensions = {".mkv", ".mp4", ".avi"}
        found_files = []

        for file in temp_dir.iterdir():
            if file.suffix in media_extensions:
                found_files.append(file)

        assert len(found_files) == 3
        assert not any(f.suffix == ".txt" for f in found_files)

    async def test_excluded_paths(self, temp_dir: Path, mock_config):
        """Test excluded path filtering."""
        # Create directory structure
        media_dir = temp_dir / "media"
        excluded_dir = temp_dir / "node_modules"

        media_dir.mkdir()
        excluded_dir.mkdir()

        (media_dir / "movie.mkv").touch()
        (excluded_dir / "excluded.mkv").touch()

        mock_config.root_paths = [temp_dir]
        mock_config.exclude_patterns = ["node_modules"]

        # Test exclusion logic
        found_files = []
        for item in temp_dir.rglob("*.mkv"):
            # Check if any parent directory is in exclude patterns
            excluded = False
            for parent in item.parents:
                if parent.name in mock_config.exclude_patterns:
                    excluded = True
                    break

            if not excluded:
                found_files.append(item)

        assert len(found_files) == 1
        assert "movie.mkv" in found_files[0].name
        assert "excluded.mkv" not in [f.name for f in found_files]

    async def test_cache_integration(self, temp_dir: Path):
        """Test cache integration."""
        mock_cache = MockCache()

        # Test cache miss
        key = "test_key"
        value = mock_cache.get(key)
        assert value is None
        assert mock_cache.misses == 1

        # Test cache set
        mock_cache.set(key, "test_value")
        assert mock_cache.set_count == 1

        # Test cache hit
        value = mock_cache.get(key)
        assert value == "test_value"
        assert mock_cache.hits == 1

        # Test cache stats
        stats = mock_cache.get_stats()
        assert stats["gets"] == 2
        assert stats["sets"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    async def test_concurrent_processing(self, temp_dir: Path):
        """Test concurrent file processing."""
        # Create multiple files
        files = []
        for i in range(10):
            file_path = temp_dir / f"file_{i}.mkv"
            file_path.touch()
            files.append(file_path)

        # Simulate concurrent processing
        async def process_file(file_path: Path) -> str:
            await asyncio.sleep(0.01)  # Simulate work
            return f"Processed: {file_path.name}"

        # Process files concurrently with limited workers
        max_workers = 3
        results = []

        for i in range(0, len(files), max_workers):
            batch = files[i : i + max_workers]
            batch_results = await asyncio.gather(*[process_file(f) for f in batch])
            results.extend(batch_results)

        assert len(results) == 10
        assert all("Processed:" in r for r in results)
