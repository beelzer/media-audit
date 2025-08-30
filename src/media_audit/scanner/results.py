"""Results module for collecting and managing scan results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from media_audit.core import EpisodeItem, MovieItem, SeasonItem, SeriesItem, ValidationStatus


@dataclass
class ScanResults:
    """Container for scan results."""

    # Timing
    scan_time: datetime = field(default_factory=datetime.now)
    duration: float = 0.0

    # Items
    movies: list[MovieItem] = field(default_factory=list)
    series: list[SeriesItem] = field(default_factory=list)

    # Errors
    errors: list[str] = field(default_factory=list)

    # Status
    cancelled: bool = False

    # Computed properties cached
    _total_items: int | None = None
    _total_issues: int | None = None

    def add_item(self, item: MovieItem | SeriesItem) -> None:
        """Add a media item to results."""
        if isinstance(item, MovieItem):
            self.movies.append(item)
        elif isinstance(item, SeriesItem):
            self.series.append(item)

        # Invalidate cache
        self._total_items = None
        self._total_issues = None

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def mark_cancelled(self) -> None:
        """Mark scan as cancelled."""
        self.cancelled = True
        self.errors.append("Scan cancelled by user")

    def finalize(self, duration: float) -> None:
        """Finalize results with duration."""
        self.duration = duration

    @property
    def total_items(self) -> int:
        """Get total number of items scanned."""
        if self._total_items is None:
            self._total_items = len(self.movies) + len(self.series)
        return self._total_items

    @property
    def total_issues(self) -> int:
        """Get total number of issues found."""
        if self._total_issues is None:
            count = 0

            # Count movie issues
            for movie in self.movies:
                count += len(movie.issues)

            # Count series issues (including seasons and episodes)
            for series in self.series:
                count += len(series.issues)
                for season in series.seasons:
                    count += len(season.issues)
                    for episode in season.episodes:
                        count += len(episode.issues)

            self._total_issues = count

        return self._total_issues

    def get_items_with_issues(self) -> list[MovieItem | SeriesItem | SeasonItem | EpisodeItem]:
        """Get all items that have issues."""
        items: list[MovieItem | SeriesItem | SeasonItem | EpisodeItem] = []

        # Check movies
        for movie in self.movies:
            if movie.issues:
                items.append(movie)

        # Check series
        for series in self.series:
            if series.issues:
                items.append(series)

            # Check seasons
            for season in series.seasons:
                if season.issues:
                    items.append(season)

                # Check episodes
                for episode in season.episodes:
                    if episode.issues:
                        items.append(episode)

        return items

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the scan."""
        error_count = 0
        warning_count = 0

        # Count all issues by severity
        for item in self.get_items_with_issues():
            for issue in item.issues:
                match issue.severity:
                    case ValidationStatus.ERROR:
                        error_count += 1
                    case ValidationStatus.WARNING:
                        warning_count += 1

        return {
            "scan_time": self.scan_time.isoformat(),
            "duration": self.duration,
            "total_items": self.total_items,
            "movies": len(self.movies),
            "series": len(self.series),
            "total_issues": self.total_issues,
            "errors": error_count,
            "warnings": warning_count,
            "scan_errors": len(self.errors),
            "cancelled": self.cancelled,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert results to dictionary for serialization."""
        return {
            "scan_time": self.scan_time.isoformat(),
            "duration": self.duration,
            "stats": self.get_stats(),
            "movies": [movie.to_dict() for movie in self.movies],
            "series": [series.to_dict() for series in self.series],
            "errors": self.errors,
            "cancelled": self.cancelled,
        }
