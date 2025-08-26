"""Tests for data models."""

from pathlib import Path

from media_audit.models import (
    CodecType,
    EpisodeItem,
    MediaAssets,
    MediaType,
    MovieItem,
    ScanResult,
    SeasonItem,
    SeriesItem,
    ValidationIssue,
    ValidationStatus,
    VideoInfo,
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
        type=MediaType.MOVIE,
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
        type=MediaType.TV_SERIES,
    )

    assert series.type == MediaType.TV_SERIES
    assert series.total_episodes == 0

    # Add a season with episodes
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


def test_scan_result():
    """Test ScanResult creation and statistics."""
    from datetime import datetime

    # Create scan result with some media items
    scan_result = ScanResult(
        scan_time=datetime.now(),
        duration=10.5,
        root_paths=[Path("/media/Movies"), Path("/media/TV")],
    )

    assert scan_result.total_items == 0
    assert scan_result.total_issues == 0

    # Add a movie with issues
    movie = MovieItem(
        path=Path("/media/Movies/Test Movie"),
        name="Test Movie",
        type=MediaType.MOVIE,
        year=2023,
    )
    movie.issues.append(
        ValidationIssue(
            category="video",
            message="Low bitrate",
            severity=ValidationStatus.WARNING,
        )
    )
    scan_result.movies.append(movie)

    # Add a series with seasons and episodes
    series = SeriesItem(
        path=Path("/media/TV/Test Series"),
        name="Test Series",
        type=MediaType.TV_SERIES,
    )

    season = SeasonItem(
        path=Path("/media/TV/Test Series/Season 01"),
        name="Season 01",
        type=MediaType.TV_SEASON,
        season_number=1,
    )
    season.issues.append(
        ValidationIssue(
            category="naming",
            message="Incorrect naming pattern",
            severity=ValidationStatus.ERROR,
        )
    )

    episode = EpisodeItem(
        path=Path("/media/TV/Test Series/Season 01"),
        name="S01E01",
        type=MediaType.TV_EPISODE,
        season_number=1,
        episode_number=1,
    )
    episode.issues.append(
        ValidationIssue(
            category="assets",
            message="Missing thumbnail",
            severity=ValidationStatus.WARNING,
        )
    )

    season.episodes.append(episode)
    series.seasons.append(season)
    series.update_episode_count()
    scan_result.series.append(series)

    # Update stats and verify
    scan_result.update_stats()
    assert scan_result.total_items == 2  # 1 movie + 1 series
    assert scan_result.total_issues == 3  # 1 movie issue + 1 season issue + 1 episode issue

    # Test get_items_with_issues
    items_with_issues = scan_result.get_items_with_issues()
    assert len(items_with_issues) == 3  # movie, season, episode
    assert movie in items_with_issues
    assert season in items_with_issues
    assert episode in items_with_issues


def test_video_info():
    """Test VideoInfo dataclass."""
    video = VideoInfo(
        path=Path("/media/test.mp4"),
        codec=CodecType.HEVC,
        resolution=(1920, 1080),
        duration=7200.0,
        bitrate=5000000,
        size=4500000000,
    )

    assert video.codec == CodecType.HEVC
    assert video.resolution == (1920, 1080)
    assert video.duration == 7200.0
    assert video.bitrate == 5000000
    assert video.size == 4500000000


def test_validation_status_priority():
    """Test validation status priority in media items."""
    movie = MovieItem(
        path=Path("/media/Movies/Test"),
        name="Test",
        type=MediaType.MOVIE,
    )

    # Initially valid
    assert movie.status == ValidationStatus.VALID

    # Add warning - should be warning
    movie.issues.append(
        ValidationIssue(
            category="test",
            message="Warning issue",
            severity=ValidationStatus.WARNING,
        )
    )
    assert movie.status == ValidationStatus.WARNING

    # Add error - should override warning
    movie.issues.append(
        ValidationIssue(
            category="test",
            message="Error issue",
            severity=ValidationStatus.ERROR,
        )
    )
    assert movie.status == ValidationStatus.ERROR

    # Add another warning - should still be error
    movie.issues.append(
        ValidationIssue(
            category="test",
            message="Another warning",
            severity=ValidationStatus.WARNING,
        )
    )
    assert movie.status == ValidationStatus.ERROR
