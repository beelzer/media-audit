"""Tests for media validator."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from media_audit.config import ScanConfig
from media_audit.models import (
    CodecType,
    EpisodeItem,
    MediaAssets,
    MediaType,
    MovieItem,
    SeasonItem,
    SeriesItem,
    ValidationStatus,
    VideoInfo,
)
from media_audit.validator import MediaValidator


@pytest.fixture
def scan_config():
    """Create a test scan configuration."""
    return ScanConfig(
        allowed_codecs=[CodecType.HEVC, CodecType.AV1, CodecType.H264],
    )


@pytest.fixture
def validator(scan_config):
    """Create a validator with test configuration."""
    return MediaValidator(scan_config)


def test_validate_movie_missing_assets(validator):
    """Test validation of movie with missing assets."""
    movie = MovieItem(
        path=Path("/media/Movies/Test Movie"),
        name="Test Movie",
        type=MediaType.MOVIE,
    )
    
    validator.validate_movie(movie)
    
    # Should have issues for missing assets
    assert len(movie.issues) >= 2
    assert any(issue.message == "Missing poster image" for issue in movie.issues)
    assert any(issue.message == "Missing background/fanart image" for issue in movie.issues)


def test_validate_movie_with_assets(validator):
    """Test validation of movie with all required assets."""
    movie = MovieItem(
        path=Path("/media/Movies/Test Movie"),
        name="Test Movie",
        type=MediaType.MOVIE,
    )
    movie.assets.posters.append(Path("/media/Movies/Test Movie/poster.jpg"))
    movie.assets.backgrounds.append(Path("/media/Movies/Test Movie/fanart.jpg"))
    movie.video_info = VideoInfo(
        path=Path("/media/Movies/Test Movie/movie.mkv"),
        codec=CodecType.HEVC,
        resolution=(1920, 1080),
        bitrate=10000000,
    )
    
    validator.validate_movie(movie)
    
    # Should have no critical issues
    errors = [issue for issue in movie.issues if issue.severity == ValidationStatus.ERROR]
    assert len(errors) == 0


def test_validate_movie_invalid_codec(validator):
    """Test validation of movie with unsupported codec."""
    movie = MovieItem(
        path=Path("/media/Movies/Test Movie"),
        name="Test Movie",
        type=MediaType.MOVIE,
    )
    movie.assets.posters.append(Path("/media/Movies/Test Movie/poster.jpg"))
    movie.assets.backgrounds.append(Path("/media/Movies/Test Movie/fanart.jpg"))
    movie.video_info = VideoInfo(
        path=Path("/media/Movies/Test Movie/movie.mkv"),
        codec=CodecType.MPEG2,  # Not in allowed codecs
        resolution=(1920, 1080),
        bitrate=10000000,
    )
    
    validator.validate_movie(movie)
    
    # Should have codec issue
    codec_issues = [issue for issue in movie.issues if "codec" in issue.message.lower()]
    assert len(codec_issues) > 0


def test_validate_episode_naming(validator):
    """Test validation of episode naming."""
    episode = EpisodeItem(
        path=Path("/media/TV/Test Series/Season 01"),
        name="S01E01",
        type=MediaType.TV_EPISODE,
        season_number=1,
        episode_number=1,
    )
    
    validator.validate_episode(episode)
    
    # Basic episode should validate without critical errors
    errors = [issue for issue in episode.issues if issue.severity == ValidationStatus.ERROR]
    assert len(errors) <= 1  # May have video file missing error


def test_validate_series_structure(validator):
    """Test validation of series structure."""
    series = SeriesItem(
        path=Path("/media/TV/Test Series"),
        name="Test Series",
        type=MediaType.TV_SERIES,
    )
    
    # Add season with episode
    season = SeasonItem(
        path=Path("/media/TV/Test Series/Season 01"),
        name="Season 01",
        type=MediaType.TV_SEASON,
        season_number=1,
    )
    
    episode = EpisodeItem(
        path=Path("/media/TV/Test Series/Season 01"),
        name="S01E01",
        type=MediaType.TV_EPISODE,
        season_number=1,
        episode_number=1,
    )
    
    season.episodes.append(episode)
    series.seasons.append(season)
    series.update_episode_count()
    
    validator.validate_series(series)
    
    # Should have issue for missing series poster
    assert any(issue.message == "Missing series poster" for issue in series.issues)


def test_validate_resolution(validator):
    """Test that resolution validation is not implemented."""
    movie = MovieItem(
        path=Path("/media/Movies/Test Movie"),
        name="Test Movie",
        type=MediaType.MOVIE,
    )
    movie.assets.posters.append(Path("poster.jpg"))
    movie.assets.backgrounds.append(Path("fanart.jpg"))
    
    # Test low resolution
    movie.video_info = VideoInfo(
        path=Path("/media/Movies/Test Movie/movie.mkv"),
        codec=CodecType.HEVC,
        resolution=(1280, 720),  # Low resolution
        bitrate=10000000,
    )
    
    validator.validate_movie(movie)
    
    # Should not have resolution issue (resolution validation not implemented)
    resolution_issues = [issue for issue in movie.issues if "resolution" in issue.message.lower()]
    assert len(resolution_issues) == 0


def test_validate_bitrate(validator):
    """Test that bitrate validation is not implemented."""
    movie = MovieItem(
        path=Path("/media/Movies/Test Movie"),
        name="Test Movie",
        type=MediaType.MOVIE,
    )
    movie.assets.posters.append(Path("poster.jpg"))
    movie.assets.backgrounds.append(Path("fanart.jpg"))
    
    # Test low bitrate
    movie.video_info = VideoInfo(
        path=Path("/media/Movies/Test Movie/movie.mkv"),
        codec=CodecType.HEVC,
        resolution=(1920, 1080),
        bitrate=1000000,  # Low bitrate
    )
    
    validator.validate_movie(movie)
    
    # Should not have bitrate issue (bitrate validation not implemented)
    bitrate_issues = [issue for issue in movie.issues if "bitrate" in issue.message.lower()]
    assert len(bitrate_issues) == 0


def test_validate_general_item(validator):
    """Test validate dispatches to correct validator."""
    # Test movie dispatch
    movie = MovieItem(
        path=Path("/media/Movies/Test"),
        name="Test",
        type=MediaType.MOVIE,
    )
    with patch.object(validator, 'validate_movie') as mock_validate:
        validator.validate(movie)
        mock_validate.assert_called_once_with(movie)
    
    # Test series dispatch  
    series = SeriesItem(
        path=Path("/media/TV/Test"),
        name="Test",
        type=MediaType.TV_SERIES,
    )
    with patch.object(validator, 'validate_series') as mock_validate:
        validator.validate(series)
        mock_validate.assert_called_once_with(series)
    
    # Test season dispatch
    season = SeasonItem(
        path=Path("/media/TV/Test/Season 01"),
        name="Season 01",
        type=MediaType.TV_SEASON,
    )
    with patch.object(validator, 'validate_season') as mock_validate:
        validator.validate(season)
        mock_validate.assert_called_once_with(season)
    
    # Test episode dispatch
    episode = EpisodeItem(
        path=Path("/media/TV/Test/Season 01"),
        name="S01E01",
        type=MediaType.TV_EPISODE,
    )
    with patch.object(validator, 'validate_episode') as mock_validate:
        validator.validate(episode)
        mock_validate.assert_called_once_with(episode)