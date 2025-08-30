"""Unit tests for scanner configuration module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from media_audit.scanner.config import ScannerConfig


class TestScannerConfig:
    """Test ScannerConfig class."""

    @pytest.fixture
    def temp_paths(self):
        """Create temporary paths for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            media_path = path / "media"
            media_path.mkdir()
            cache_path = path / "cache"
            cache_path.mkdir()
            yield media_path, cache_path

    def test_default_config(self, temp_paths):
        """Test default scanner configuration."""
        media_path, cache_path = temp_paths

        config = ScannerConfig(
            root_paths=[media_path],
            cache_dir=cache_path,
        )

        assert config.root_paths == [media_path]
        assert config.cache_dir == cache_path
        assert config.cache_enabled is True
        assert config.concurrent_workers == 8  # Default is 8
        assert config.profiles == ["plex", "jellyfin"]  # Default profiles
        assert config.allowed_codecs == ["hevc", "h265", "av1"]  # Default codecs
        assert config.auto_open is True
        assert config.problems_only is False
        assert len(config.exclude_patterns) > 0  # Has default exclusions

    def test_custom_config(self, temp_paths):
        """Test custom scanner configuration."""
        media_path, cache_path = temp_paths

        config = ScannerConfig(
            root_paths=[media_path],
            cache_dir=cache_path,
            cache_enabled=False,
            concurrent_workers=4,
            profiles=["custom"],
            allowed_codecs=["h264", "h265"],
            auto_open=False,
            problems_only=True,
        )

        assert config.cache_enabled is False
        assert config.concurrent_workers == 4
        assert config.profiles == ["custom"]
        assert config.allowed_codecs == ["h264", "h265"]
        assert config.auto_open is False
        assert config.problems_only is True

    def test_exclude_patterns(self, temp_paths):
        """Test default exclude patterns."""
        media_path, cache_path = temp_paths

        config = ScannerConfig(
            root_paths=[media_path],
            cache_dir=cache_path,
        )

        # Check some default exclusions
        assert "*.sample.*" in config.exclude_patterns
        assert "**/Extras/**" in config.exclude_patterns
        assert "**/.AppleDouble/**" in config.exclude_patterns

    def test_custom_exclude_patterns(self, temp_paths):
        """Test custom exclude patterns."""
        media_path, cache_path = temp_paths

        config = ScannerConfig(
            root_paths=[media_path],
            cache_dir=cache_path,
            exclude_patterns=["**/test/**", "*.tmp"],
        )

        assert "**/test/**" in config.exclude_patterns
        assert "*.tmp" in config.exclude_patterns

    def test_include_patterns(self, temp_paths):
        """Test include patterns configuration."""
        media_path, cache_path = temp_paths

        config = ScannerConfig(
            root_paths=[media_path],
            cache_dir=cache_path,
            include_patterns=["*.mkv", "*.mp4"],
        )

        assert "*.mkv" in config.include_patterns
        assert "*.mp4" in config.include_patterns

    def test_output_paths(self, temp_paths):
        """Test output path configuration."""
        media_path, cache_path = temp_paths

        config = ScannerConfig(
            root_paths=[media_path],
            cache_dir=cache_path,
        )

        # Default output path
        assert config.output_path == Path("media-audit-report.html")
        assert config.json_path is None

        # Custom paths
        custom_config = ScannerConfig(
            root_paths=[media_path],
            cache_dir=cache_path,
            output_path=Path("/tmp/report.html"),
            json_path=Path("/tmp/report.json"),
        )

        assert custom_config.output_path == Path("/tmp/report.html")
        assert custom_config.json_path == Path("/tmp/report.json")

    def test_multiple_root_paths(self, temp_paths):
        """Test configuration with multiple root paths."""
        media_path, cache_path = temp_paths

        # Create additional paths
        movies_path = media_path / "movies"
        movies_path.mkdir()
        tv_path = media_path / "tv"
        tv_path.mkdir()

        config = ScannerConfig(
            root_paths=[movies_path, tv_path],
            cache_dir=cache_path,
        )

        assert len(config.root_paths) == 2
        assert movies_path in config.root_paths
        assert tv_path in config.root_paths

    def test_from_file(self, temp_paths):
        """Test loading configuration from YAML file."""
        media_path, cache_path = temp_paths

        # Create a config file
        config_file = cache_path / "config.yaml"
        config_data = {
            "scan": {
                "root_paths": [str(media_path)],
                "cache_dir": str(cache_path),
                "concurrent_workers": 4,
                "profiles": ["test"],
                "allowed_codecs": ["h264"],
            }
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Load config from file
        config = ScannerConfig.from_file(config_file)

        assert len(config.root_paths) == 1
        assert config.root_paths[0] == Path(media_path)
        assert config.cache_dir == Path(cache_path)
        assert config.concurrent_workers == 4
        assert config.profiles == ["test"]
        assert config.allowed_codecs == ["h264"]

    def test_from_dict(self, temp_paths):
        """Test creating config from dictionary."""
        media_path, cache_path = temp_paths

        config_data = {
            "scan": {
                "root_paths": [str(media_path)],
                "cache_dir": str(cache_path),
                "concurrent_workers": 4,
            }
        }

        config = ScannerConfig.from_dict(config_data)

        assert len(config.root_paths) == 1
        assert config.root_paths[0] == Path(media_path)
        assert config.cache_dir == Path(cache_path)
        assert config.concurrent_workers == 4

    def test_config_with_none_cache_dir(self, temp_paths):
        """Test configuration with None cache_dir."""
        media_path, _ = temp_paths

        config = ScannerConfig(
            root_paths=[media_path],
            cache_dir=None,
        )

        assert config.cache_dir is None
        assert config.root_paths == [media_path]
