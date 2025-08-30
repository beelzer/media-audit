"""Unit tests for scanner results module."""

from datetime import datetime
from pathlib import Path

import pytest

from media_audit.core import (
    EpisodeItem,
    MediaType,
    MovieItem,
    SeasonItem,
    SeriesItem,
    ValidationStatus,
)
from media_audit.scanner.results import ScanResults


class TestScanResults:
    """Test ScanResults class."""

    @pytest.fixture
    def empty_results(self):
        """Create empty scan results."""
        return ScanResults()

    @pytest.fixture
    def sample_movie(self):
        """Create a sample movie item."""
        movie = MovieItem(
            path=Path("/media/movies/test"),
            name="Test Movie",
            type=MediaType.MOVIE,
            year=2024,
        )
        movie.add_issue(
            category="quality",
            message="Low bitrate detected",
            severity=ValidationStatus.WARNING,
        )
        return movie

    @pytest.fixture
    def sample_series(self):
        """Create a sample series with seasons and episodes."""
        series = SeriesItem(
            path=Path("/media/tv/test"),
            name="Test Series",
            type=MediaType.TV_SERIES,
        )

        season = SeasonItem(
            path=Path("/media/tv/test/Season 01"),
            name="Season 01",
            type=MediaType.TV_SEASON,
            season_number=1,
        )

        episode = EpisodeItem(
            path=Path("/media/tv/test/Season 01/S01E01.mkv"),
            name="S01E01",
            type=MediaType.TV_EPISODE,
            season_number=1,
            episode_number=1,
        )
        episode.add_issue(
            category="codec",
            message="Unsupported codec",
            severity=ValidationStatus.ERROR,
        )

        season.episodes.append(episode)
        series.seasons.append(season)

        return series

    def test_initialization(self, empty_results):
        """Test ScanResults initialization."""
        assert empty_results.scan_time is not None
        assert isinstance(empty_results.scan_time, datetime)
        assert empty_results.duration == 0.0
        assert empty_results.movies == []
        assert empty_results.series == []
        assert empty_results.errors == []
        assert empty_results.cancelled is False
        assert empty_results.total_items == 0
        assert empty_results.total_issues == 0

    def test_add_movie(self, empty_results, sample_movie):
        """Test adding a movie to results."""
        empty_results.add_item(sample_movie)

        assert len(empty_results.movies) == 1
        assert empty_results.movies[0] == sample_movie
        assert empty_results.total_items == 1
        assert empty_results.total_issues == 1

    def test_add_series(self, empty_results, sample_series):
        """Test adding a series to results."""
        empty_results.add_item(sample_series)

        assert len(empty_results.series) == 1
        assert empty_results.series[0] == sample_series
        assert empty_results.total_items == 1
        assert empty_results.total_issues == 1  # One issue in episode

    def test_add_error(self, empty_results):
        """Test adding error messages."""
        error_msg = "Failed to process file"
        empty_results.add_error(error_msg)

        assert len(empty_results.errors) == 1
        assert empty_results.errors[0] == error_msg

    def test_mark_cancelled(self, empty_results):
        """Test marking scan as cancelled."""
        empty_results.mark_cancelled()

        assert empty_results.cancelled is True
        assert len(empty_results.errors) == 1
        assert "cancelled" in empty_results.errors[0].lower()

    def test_finalize(self, empty_results):
        """Test finalizing results with duration."""
        duration = 10.5
        empty_results.finalize(duration)

        assert empty_results.duration == duration

    def test_total_items_calculation(self, empty_results, sample_movie, sample_series):
        """Test total items calculation."""
        empty_results.add_item(sample_movie)
        empty_results.add_item(sample_series)

        assert empty_results.total_items == 2

    def test_total_issues_calculation(self, empty_results, sample_movie, sample_series):
        """Test total issues calculation across all items."""
        empty_results.add_item(sample_movie)
        empty_results.add_item(sample_series)

        # Movie has 1 warning, series has 1 error in episode
        assert empty_results.total_issues == 2

    def test_get_items_with_issues(self, empty_results, sample_movie, sample_series):
        """Test getting all items that have issues."""
        # Add movie with issue
        empty_results.add_item(sample_movie)

        # Add series with issue in episode
        empty_results.add_item(sample_series)

        # Add movie without issues
        clean_movie = MovieItem(
            path=Path("/media/movies/clean"),
            name="Clean Movie",
            type=MediaType.MOVIE,
        )
        empty_results.add_item(clean_movie)

        items_with_issues = empty_results.get_items_with_issues()

        # Should have movie and episode with issues
        assert len(items_with_issues) == 2
        assert sample_movie in items_with_issues
        # The episode with issues should be in the list
        assert any(hasattr(item, "episode_number") for item in items_with_issues)

    def test_get_stats(self, empty_results, sample_movie, sample_series):
        """Test getting statistics about the scan."""
        empty_results.add_item(sample_movie)
        empty_results.add_item(sample_series)
        empty_results.finalize(5.0)
        empty_results.add_error("Test error")

        stats = empty_results.get_stats()

        assert stats["duration"] == 5.0
        assert stats["total_items"] == 2
        assert stats["movies"] == 1
        assert stats["series"] == 1
        assert stats["total_issues"] == 2
        assert stats["errors"] == 1
        assert stats["warnings"] == 1
        assert stats["scan_errors"] == 1
        assert stats["cancelled"] is False

    def test_to_dict(self, empty_results, sample_movie):
        """Test converting results to dictionary."""
        empty_results.add_item(sample_movie)
        empty_results.finalize(2.5)

        result_dict = empty_results.to_dict()

        assert "scan_time" in result_dict
        assert result_dict["duration"] == 2.5
        assert "stats" in result_dict
        assert "movies" in result_dict
        assert len(result_dict["movies"]) == 1
        assert "series" in result_dict
        assert result_dict["cancelled"] is False

    def test_cache_invalidation(self, empty_results, sample_movie):
        """Test that cache is invalidated when items are added."""
        # Access properties to cache them
        _ = empty_results.total_items
        _ = empty_results.total_issues

        # Add item which should invalidate cache
        empty_results.add_item(sample_movie)

        # Properties should reflect new state
        assert empty_results.total_items == 1
        assert empty_results.total_issues == 1

    def test_complex_series_issues(self, empty_results):
        """Test counting issues in complex series structure."""
        series = SeriesItem(
            path=Path("/media/tv/complex"),
            name="Complex Series",
            type=MediaType.TV_SERIES,
        )
        series.add_issue("format", "Missing NFO", ValidationStatus.WARNING)

        # Add season with issue
        season1 = SeasonItem(
            path=Path("/media/tv/complex/Season 01"),
            name="Season 01",
            type=MediaType.TV_SEASON,
            season_number=1,
        )
        season1.add_issue("structure", "Incorrect naming", ValidationStatus.WARNING)

        # Add episodes with issues
        for i in range(3):
            episode = EpisodeItem(
                path=Path(f"/media/tv/complex/Season 01/S01E{i + 1:02d}.mkv"),
                name=f"S01E{i + 1:02d}",
                type=MediaType.TV_EPISODE,
                season_number=1,
                episode_number=i + 1,
            )
            episode.add_issue("quality", f"Low quality episode {i + 1}", ValidationStatus.ERROR)
            season1.episodes.append(episode)

        series.seasons.append(season1)
        empty_results.add_item(series)

        # Should have 1 series issue + 1 season issue + 3 episode issues = 5 total
        assert empty_results.total_issues == 5

        items_with_issues = empty_results.get_items_with_issues()
        assert len(items_with_issues) == 5  # series, season, and 3 episodes
