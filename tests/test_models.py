"""Tests for data models."""

from pathlib import Path

import pytest

from media_audit.models import (
    MediaType,
    ValidationStatus,
    CodecType,
    ValidationIssue,
    MediaAssets,
    MovieItem,
    SeriesItem,
    SeasonItem,
    EpisodeItem,
)


def test_validation_issue():
    """Test ValidationIssue creation."""
    issue = ValidationIssue(
        category="assets",
        message="Missing poster",
        severity=ValidationStatus.ERROR,
        details={"expected": "poster.jpg"},
    )
    
    assert issue.category == "assets"
    assert issue.message == "Missing poster"
    assert issue.severity == ValidationStatus.ERROR
    assert issue.details == {"expected": "poster.jpg"}


def test_movie_item():
    """Test MovieItem creation and validation status."""
    movie = MovieItem(
        path=Path("/media/Movies/Test Movie (2023)"),
        name="Test Movie",
        year=2023,
    )
    
    assert movie.type == MediaType.MOVIE
    assert movie.name == "Test Movie"
    assert movie.year == 2023
    assert movie.status == ValidationStatus.VALID
    assert not movie.has_issues
    
    # Add an error
    movie.issues.append(
        ValidationIssue(
            category="test",
            message="Test error",
            severity=ValidationStatus.ERROR,
        )
    )
    
    assert movie.status == ValidationStatus.ERROR
    assert movie.has_issues


def test_series_item():
    """Test SeriesItem with seasons and episodes."""
    series = SeriesItem(
        path=Path("/media/TV/Test Series"),
        name="Test Series",
    )
    
    assert series.type == MediaType.TV_SERIES
    assert series.total_episodes == 0
    
    # Add a season with episodes
    season = SeasonItem(
        path=Path("/media/TV/Test Series/Season 01"),
        name="Season 01",
        season_number=1,
    )
    
    episode = EpisodeItem(
        path=Path("/media/TV/Test Series/Season 01"),
        name="S01E01",
        season_number=1,
        episode_number=1,
    )
    
    season.episodes.append(episode)
    series.seasons.append(season)
    series.update_episode_count()
    
    assert series.total_episodes == 1
    assert len(series.seasons) == 1
    assert len(series.seasons[0].episodes) == 1


def test_codec_types():
    """Test codec type enumeration."""
    assert CodecType.HEVC.value == "hevc"
    assert CodecType.AV1.value == "av1"
    assert CodecType.H264.value == "h264"


def test_media_assets():
    """Test MediaAssets container."""
    assets = MediaAssets()
    
    assert assets.posters == []
    assert assets.backgrounds == []
    assert assets.banners == []
    assert assets.trailers == []
    assert assets.title_cards == []
    
    # Add some assets
    assets.posters.append(Path("/media/poster.jpg"))
    assets.backgrounds.append(Path("/media/fanart.jpg"))
    
    assert len(assets.posters) == 1
    assert len(assets.backgrounds) == 1