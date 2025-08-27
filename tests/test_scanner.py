"""Tests for media scanner."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from media_audit.core import CodecType, MediaType, MovieItem, SeriesItem
from media_audit.domain.patterns import get_patterns
from media_audit.domain.scanning import MediaScanner
from media_audit.infrastructure.config import ScanConfig


@pytest.fixture
def scan_config():
    """Create test scan configuration."""
    return ScanConfig(
        root_paths=[Path("/media")],
        patterns=get_patterns(),
        allowed_codecs=[CodecType.HEVC, CodecType.H264],
    )


@pytest.fixture
def scanner(scan_config):
    """Create scanner with test configuration."""
    return MediaScanner(scan_config)


def test_scanner_initialization(scan_config):
    """Test scanner initialization."""
    scanner = MediaScanner(scan_config)
    assert scanner.config == scan_config
    assert scanner.movie_parser is not None
    assert scanner.tv_parser is not None
    assert scanner.validator is not None


def test_scanner_initialization_no_patterns():
    """Test scanner initialization with auto-generated patterns."""
    config = ScanConfig(
        root_paths=[Path("/media")],
        patterns=None,  # Will be auto-generated in __post_init__
    )
    scanner = MediaScanner(config)
    assert scanner.config.patterns is not None


def test_scan_nonexistent_path(scanner, tmp_path):
    """Test scanning with non-existent path."""
    scanner.config.root_paths = [tmp_path / "nonexistent"]

    result = scanner.scan()

    assert len(result.errors) == 1
    assert "Root path does not exist" in result.errors[0]
    assert result.total_items == 0


def test_scan_empty_directory(scanner, tmp_path):
    """Test scanning empty directory."""
    scanner.config.root_paths = [tmp_path]

    result = scanner.scan()

    assert len(result.errors) == 0
    assert result.total_items == 0
    assert len(result.movies) == 0
    assert len(result.series) == 0


def test_scan_with_movies(scanner, tmp_path):
    """Test scanning directory with movie structure."""
    # Create movie directory structure
    movies_dir = tmp_path / "Movies"
    movies_dir.mkdir()
    movie_dir = movies_dir / "Test Movie (2023)"
    movie_dir.mkdir()
    (movie_dir / "Test Movie (2023).mkv").touch()
    (movie_dir / "poster.jpg").touch()

    scanner.config.root_paths = [tmp_path]

    with patch.object(scanner.movie_parser, "parse") as mock_parse:
        mock_movie = MovieItem(
            path=movie_dir,
            name="Test Movie",
            type=MediaType.MOVIE,
            year=2023,
        )
        mock_parse.return_value = mock_movie

        result = scanner.scan()

        assert len(result.movies) == 1
        assert result.movies[0].name == "Test Movie"


def test_scan_with_tv_shows(scanner, tmp_path):
    """Test scanning directory with TV show structure."""
    # Create TV show directory structure
    tv_dir = tmp_path / "TV"
    tv_dir.mkdir()
    series_dir = tv_dir / "Test Series"
    series_dir.mkdir()
    season_dir = series_dir / "Season 01"
    season_dir.mkdir()
    (season_dir / "S01E01.mkv").touch()

    scanner.config.root_paths = [tmp_path]

    with patch.object(scanner.tv_parser, "parse") as mock_parse:
        mock_series = SeriesItem(
            path=series_dir,
            name="Test Series",
            type=MediaType.TV_SERIES,
        )
        mock_parse.return_value = mock_series

        result = scanner.scan()

        assert len(result.series) == 1
        assert result.series[0].name == "Test Series"


def test_scan_validates_items(scanner, tmp_path):
    """Test that scanner validates found items."""
    movies_dir = tmp_path / "Movies"
    movies_dir.mkdir()
    movie_dir = movies_dir / "Test Movie"
    movie_dir.mkdir()

    scanner.config.root_paths = [tmp_path]

    with patch.object(scanner.movie_parser, "parse") as mock_parse:
        mock_movie = MovieItem(
            path=movie_dir,
            name="Test Movie",
            type=MediaType.MOVIE,
        )
        mock_parse.return_value = mock_movie

        with patch.object(scanner.validator, "validate_movie") as mock_validate:
            scanner.scan()

            # Validator should have been called
            mock_validate.assert_called_with(mock_movie)


def test_scan_parallel_processing(scanner, tmp_path):
    """Test parallel processing of items."""
    movies_dir = tmp_path / "Movies"
    movies_dir.mkdir()

    # Create multiple movies
    for i in range(3):
        movie_dir = movies_dir / f"Movie {i}"
        movie_dir.mkdir()
        (movie_dir / f"movie{i}.mkv").touch()

    scanner.config.root_paths = [tmp_path]
    scanner.config.max_workers = 2  # Use parallel processing

    with patch.object(scanner.movie_parser, "parse") as mock_parse:
        mock_parse.side_effect = [
            MovieItem(
                path=movies_dir / f"Movie {i}",
                name=f"Movie {i}",
                type=MediaType.MOVIE,
            )
            for i in range(3)
        ]

        result = scanner.scan()

        assert len(result.movies) == 3


def test_scan_stats_update(scanner):
    """Test that scan result stats are updated."""
    with patch.object(scanner, "_scan_path"):
        result = scanner.scan()

        assert result.duration > 0
        assert isinstance(result.scan_time, datetime)
        assert result.root_paths == scanner.config.root_paths


def test_scan_path_movies_and_tv(scanner, tmp_path):
    """Test scanning path with both movies and TV shows."""
    # Create both Movies and TV directories
    movies_dir = tmp_path / "Movies"
    movies_dir.mkdir()
    tv_dir = tmp_path / "TV Shows"
    tv_dir.mkdir()

    scanner.config.root_paths = [tmp_path]

    with (
        patch.object(scanner, "_scan_movies") as mock_scan_movies,
        patch.object(scanner, "_scan_tv_shows") as mock_scan_tv,
    ):
        scanner.scan()

        # Both scan methods should be called
        mock_scan_movies.assert_called()
        mock_scan_tv.assert_called()
