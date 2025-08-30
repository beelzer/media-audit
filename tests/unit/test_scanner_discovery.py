"""Unit tests for scanner discovery module."""

import tempfile
from pathlib import Path

import pytest

from media_audit.scanner.config import ScannerConfig
from media_audit.scanner.discovery import PathDiscovery


class TestPathDiscovery:
    """Test PathDiscovery class."""

    @pytest.fixture
    def temp_media_structure(self):
        """Create a temporary media directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create movie directories
            movies = root / "Movies"
            movies.mkdir()
            (movies / "Movie1 (2023)").mkdir()
            (movies / "Movie1 (2023)" / "Movie1.mkv").touch()
            (movies / "Movie2 (2024)").mkdir()
            (movies / "Movie2 (2024)" / "Movie2.mp4").touch()

            # Create TV directories
            tv = root / "TV Shows"
            tv.mkdir()
            show1 = tv / "Show1"
            show1.mkdir()
            (show1 / "Season 01").mkdir()
            (show1 / "Season 01" / "S01E01.mkv").touch()
            (show1 / "Season 01" / "S01E02.mkv").touch()
            (show1 / "Season 02").mkdir()
            (show1 / "Season 02" / "S02E01.mkv").touch()

            show2 = tv / "Show2"
            show2.mkdir()
            (show2 / "Season 01").mkdir()
            (show2 / "Season 01" / "S01E01.mp4").touch()

            # Create hidden directory
            hidden = root / ".hidden"
            hidden.mkdir()
            (hidden / "HiddenMovie").mkdir()

            # Create empty directory
            (root / "empty").mkdir()

            # Create file at root (should be ignored)
            (root / "readme.txt").touch()

            yield root

    @pytest.fixture
    def config(self, temp_media_structure):
        """Create scanner config with temp paths."""
        return ScannerConfig(
            root_paths=[temp_media_structure],
            cache_dir=temp_media_structure / ".cache",
        )

    def test_discovery_initialization(self, config):
        """Test PathDiscovery initialization."""
        discovery = PathDiscovery(config)

        assert discovery.config == config
        assert hasattr(discovery, "logger")

    def test_discover_library_structure(self, config, temp_media_structure):
        """Test discovering media in library structure."""
        discovery = PathDiscovery(config)

        # Discover from root which has Movies and TV Shows
        paths = discovery.discover(temp_media_structure)

        # Should find 4 media items (2 movies + 2 TV shows)
        assert len(paths) == 4

        # Check that correct directories were found
        path_names = [p.name for p in paths]
        assert "Movie1 (2023)" in path_names
        assert "Movie2 (2024)" in path_names
        assert "Show1" in path_names
        assert "Show2" in path_names

    def test_discover_movies_directory(self, config, temp_media_structure):
        """Test discovering from Movies directory."""
        discovery = PathDiscovery(config)

        movies_path = temp_media_structure / "Movies"
        paths = discovery.discover(movies_path)

        # Should find 2 movies
        assert len(paths) == 2
        path_names = [p.name for p in paths]
        assert "Movie1 (2023)" in path_names
        assert "Movie2 (2024)" in path_names

    def test_discover_tv_shows_directory(self, config, temp_media_structure):
        """Test discovering from TV Shows directory."""
        discovery = PathDiscovery(config)

        tv_path = temp_media_structure / "TV Shows"
        paths = discovery.discover(tv_path)

        # Should find 2 TV shows
        assert len(paths) == 2
        path_names = [p.name for p in paths]
        assert "Show1" in path_names
        assert "Show2" in path_names

    def test_discover_single_media_item(self, config, temp_media_structure):
        """Test discovering a single media item directory."""
        discovery = PathDiscovery(config)

        # Point directly to a movie
        movie_path = temp_media_structure / "Movies" / "Movie1 (2023)"
        paths = discovery.discover(movie_path)

        # Should return the directory itself
        assert len(paths) == 1
        assert paths[0] == movie_path

    def test_is_library_root(self, config, temp_media_structure):
        """Test library root detection."""
        discovery = PathDiscovery(config)

        # Root with Movies/TV Shows should be library root
        assert discovery._is_library_root(temp_media_structure) is True

        # Empty directory should not be library root
        empty_dir = temp_media_structure / "empty"
        assert discovery._is_library_root(empty_dir) is False

    def test_is_content_directory(self, config):
        """Test content directory detection."""
        discovery = PathDiscovery(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create movie directory with video file
            movie_dir = root / "Movie"
            movie_dir.mkdir()
            (movie_dir / "movie.mkv").touch()
            assert discovery._is_content_directory(movie_dir, None) is True

            # Create TV directory with season
            tv_dir = root / "Show"
            tv_dir.mkdir()
            (tv_dir / "Season 01").mkdir()
            assert discovery._is_content_directory(tv_dir, "tv") is True

            # Empty directory
            empty = root / "Empty"
            empty.mkdir()
            assert discovery._is_content_directory(empty, None) is False

    def test_media_extensions(self, config):
        """Test that media extensions are defined."""
        discovery = PathDiscovery(config)

        # Check that common extensions are included
        assert ".mkv" in discovery.MEDIA_EXTENSIONS
        assert ".mp4" in discovery.MEDIA_EXTENSIONS
        assert ".avi" in discovery.MEDIA_EXTENSIONS

    def test_ignore_dirs(self, config):
        """Test that certain directories are ignored."""
        discovery = PathDiscovery(config)

        # Check that system directories are ignored
        assert ".git" in discovery.IGNORE_DIRS
        assert "__pycache__" in discovery.IGNORE_DIRS
        assert "@eaDir" in discovery.IGNORE_DIRS

    def test_discover_empty_directory(self, config):
        """Test discovering with no media directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_root = Path(tmpdir)

            discovery = PathDiscovery(config)
            paths = discovery.discover(empty_root)

            # Should return empty list
            assert paths == []

    def test_discover_nonexistent_path(self, config):
        """Test discovering with nonexistent path."""
        nonexistent = Path("/nonexistent/path/that/does/not/exist")

        discovery = PathDiscovery(config)

        # Should handle gracefully (might raise or return empty)
        try:
            paths = discovery.discover(nonexistent)
            assert paths == []
        except (FileNotFoundError, OSError):
            # This is also acceptable behavior
            pass
