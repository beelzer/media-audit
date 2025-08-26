"""Tests for media parsers."""

from pathlib import Path

from media_audit.parsers import MovieParser, TVParser
from media_audit.patterns import PLEX_PATTERNS


def test_movie_parser_year_extraction():
    """Test year extraction from movie folder names."""
    patterns = PLEX_PATTERNS.compile_patterns()
    parser = MovieParser(patterns)

    assert parser.parse_year("Movie Title (2023)") == 2023
    assert parser.parse_year("Another Movie (1999)") == 1999
    assert parser.parse_year("No Year Movie") is None
    assert parser.parse_year("Invalid (9999)") is None


def test_tv_parser_season_extraction():
    """Test season number extraction."""
    patterns = PLEX_PATTERNS.compile_patterns()
    parser = TVParser(patterns)

    assert parser.extract_season_number("Season 01") == 1
    assert parser.extract_season_number("Season 2") == 2
    assert parser.extract_season_number("S03") == 3
    assert parser.extract_season_number("Random Folder") is None


def test_tv_parser_episode_parsing():
    """Test episode information parsing."""
    patterns = PLEX_PATTERNS.compile_patterns()
    parser = TVParser(patterns)

    # Test S01E01 format
    ep_info = parser.parse_episode_info("S01E01 - Episode Title.mkv")
    assert ep_info is not None
    assert ep_info["season"] == 1
    assert ep_info["episode"] == 1

    # Test 1x01 format
    ep_info = parser.parse_episode_info("1x01.Episode.Title.mp4")
    assert ep_info is not None
    assert ep_info["season"] == 1
    assert ep_info["episode"] == 1

    # Test invalid format
    ep_info = parser.parse_episode_info("random_video.mp4")
    assert ep_info is None


def test_base_parser_video_detection():
    """Test video file detection."""
    patterns = PLEX_PATTERNS.compile_patterns()
    parser = MovieParser(patterns)

    assert parser.is_video_file(Path("movie.mkv"))
    assert parser.is_video_file(Path("show.MP4"))
    assert parser.is_video_file(Path("video.avi"))
    assert not parser.is_video_file(Path("image.jpg"))
    assert not parser.is_video_file(Path("document.pdf"))


def test_base_parser_image_detection():
    """Test image file detection."""
    patterns = PLEX_PATTERNS.compile_patterns()
    parser = MovieParser(patterns)

    assert parser.is_image_file(Path("poster.jpg"))
    assert parser.is_image_file(Path("fanart.PNG"))
    assert parser.is_image_file(Path("background.webp"))
    assert not parser.is_image_file(Path("video.mp4"))
    assert not parser.is_image_file(Path("text.txt"))
