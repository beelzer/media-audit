"""Tests for base parser functionality."""

from pathlib import Path

import pytest

from media_audit.parsers.base import BaseParser
from media_audit.patterns import get_patterns


@pytest.fixture
def base_parser():
    """Create a base parser with default patterns."""
    patterns = get_patterns()  # Get combined patterns
    compiled = patterns.compile_patterns()
    return BaseParser(compiled)


def test_is_video_file(base_parser):
    """Test video file detection."""
    assert base_parser.is_video_file(Path("test.mkv"))
    assert base_parser.is_video_file(Path("test.mp4"))
    assert base_parser.is_video_file(Path("test.avi"))
    assert base_parser.is_video_file(Path("test.MOV"))  # Case insensitive
    assert not base_parser.is_video_file(Path("test.jpg"))
    assert not base_parser.is_video_file(Path("test.txt"))


def test_is_image_file(base_parser):
    """Test image file detection."""
    assert base_parser.is_image_file(Path("test.jpg"))
    assert base_parser.is_image_file(Path("test.png"))
    assert base_parser.is_image_file(Path("test.JPEG"))  # Case insensitive
    assert not base_parser.is_image_file(Path("test.mp4"))
    assert not base_parser.is_image_file(Path("test.txt"))


def test_parse_year(base_parser):
    """Test year extraction from text."""
    assert base_parser.parse_year("Movie Title (2023)") == 2023
    assert base_parser.parse_year("(2020) - Movie") == 2020
    assert base_parser.parse_year("No year here") is None
    assert base_parser.parse_year("Invalid (1800)") is None  # Too old
    assert base_parser.parse_year("Future (2200)") is None  # Too far


def test_classify_asset(base_parser):
    """Test asset classification."""
    base_path = Path("/media")

    # Test poster classification
    poster_path = Path("/media/poster.jpg")
    result = base_parser.classify_asset(poster_path, base_path)
    assert result == ("poster", poster_path)

    # Test background classification
    background_path = Path("/media/fanart.jpg")
    result = base_parser.classify_asset(background_path, base_path)
    assert result == ("background", background_path)

    # Test trailer classification
    trailer_path = Path("/media/trailer.mp4")
    result = base_parser.classify_asset(trailer_path, base_path)
    assert result == ("trailer", trailer_path)

    # Test non-media file
    text_path = Path("/media/readme.txt")
    result = base_parser.classify_asset(text_path, base_path)
    assert result is None


def test_scan_assets(base_parser, tmp_path):
    """Test scanning directory for assets."""
    # Create test directory structure
    media_dir = tmp_path / "media"
    media_dir.mkdir()

    # Create test files
    (media_dir / "poster.jpg").touch()
    (media_dir / "fanart.jpg").touch()
    (media_dir / "banner.jpg").touch()
    (media_dir / "trailer.mp4").touch()
    (media_dir / "movie.mkv").touch()  # Should not be classified as asset
    (media_dir / "readme.txt").touch()  # Should be ignored

    # Create title card in main directory
    (media_dir / "S01E01.jpg").touch()  # Title card for episode

    # Scan for assets
    assets = base_parser.scan_assets(media_dir)

    # Verify results
    assert len(assets.posters) == 1
    assert len(assets.backgrounds) == 1
    assert len(assets.banners) == 1
    assert len(assets.trailers) == 1
    assert len(assets.title_cards) == 1


def test_match_pattern(base_parser):
    """Test pattern matching."""
    import re

    patterns = [
        re.compile(r"poster"),
        re.compile(r"cover"),
    ]

    assert base_parser.match_pattern("poster.jpg", patterns)
    assert base_parser.match_pattern("movie-cover.png", patterns)
    assert not base_parser.match_pattern("fanart.jpg", patterns)
