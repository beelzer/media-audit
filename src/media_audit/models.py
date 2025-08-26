"""Data models for media audit results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any


class MediaType(Enum):
    """Type of media content."""

    MOVIE = auto()
    TV_SERIES = auto()
    TV_SEASON = auto()
    TV_EPISODE = auto()


class ValidationStatus(Enum):
    """Validation status for media items."""

    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"


class CodecType(Enum):
    """Video codec types."""

    HEVC = "hevc"
    AV1 = "av1"
    H264 = "h264"
    H265 = "h265"
    VP9 = "vp9"
    MPEG4 = "mpeg4"
    MPEG2 = "mpeg2"
    OTHER = "other"


@dataclass
class ValidationIssue:
    """Represents a validation issue found during scanning."""

    category: str
    message: str
    severity: ValidationStatus
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoInfo:
    """Information about a video file."""

    path: Path
    codec: CodecType | None = None
    resolution: tuple[int, int] | None = None
    duration: float | None = None
    bitrate: int | None = None
    size: int = 0
    raw_info: dict[str, Any] = field(default_factory=dict)


@dataclass
class MediaAssets:
    """Collection of media assets (posters, backgrounds, etc.)."""

    posters: list[Path] = field(default_factory=list)
    backgrounds: list[Path] = field(default_factory=list)
    banners: list[Path] = field(default_factory=list)
    trailers: list[Path] = field(default_factory=list)
    title_cards: list[Path] = field(default_factory=list)


@dataclass
class MediaItem:
    """Base class for all media items."""

    path: Path
    name: str
    type: MediaType
    assets: MediaAssets = field(default_factory=MediaAssets)
    issues: list[ValidationIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> ValidationStatus:
        """Get overall validation status."""
        if any(issue.severity == ValidationStatus.ERROR for issue in self.issues):
            return ValidationStatus.ERROR
        if any(issue.severity == ValidationStatus.WARNING for issue in self.issues):
            return ValidationStatus.WARNING
        return ValidationStatus.VALID

    @property
    def has_issues(self) -> bool:
        """Check if item has any issues."""
        return len(self.issues) > 0


@dataclass
class MovieItem(MediaItem):
    """Represents a movie."""

    year: int | None = None
    video_info: VideoInfo | None = None
    imdb_id: str | None = None
    tmdb_id: str | None = None
    release_group: str | None = None
    quality: str | None = None
    source: str | None = None  # BluRay, WEBDL, WEBRip, etc.

    def __post_init__(self) -> None:
        self.type = MediaType.MOVIE


@dataclass
class EpisodeItem(MediaItem):
    """Represents a TV episode."""

    season_number: int = 0
    episode_number: int = 0
    episode_title: str | None = None
    video_info: VideoInfo | None = None
    release_group: str | None = None
    quality: str | None = None
    source: str | None = None  # WEBDL, WEBRip, HDTV, etc.

    def __post_init__(self) -> None:
        self.type = MediaType.TV_EPISODE


@dataclass
class SeasonItem(MediaItem):
    """Represents a TV season."""

    season_number: int = 0
    episodes: list[EpisodeItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = MediaType.TV_SEASON


@dataclass
class SeriesItem(MediaItem):
    """Represents a TV series."""

    seasons: list[SeasonItem] = field(default_factory=list)
    total_episodes: int = 0
    imdb_id: str | None = None
    tvdb_id: str | None = None
    tmdb_id: str | None = None

    def __post_init__(self) -> None:
        self.type = MediaType.TV_SERIES
        self.update_episode_count()

    def update_episode_count(self) -> None:
        """Update total episode count."""
        self.total_episodes = sum(len(season.episodes) for season in self.seasons)


@dataclass
class ScanResult:
    """Results from a media library scan."""

    scan_time: datetime
    duration: float
    root_paths: list[Path]
    movies: list[MovieItem] = field(default_factory=list)
    series: list[SeriesItem] = field(default_factory=list)
    total_items: int = 0
    total_issues: int = 0
    errors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.update_stats()

    def update_stats(self) -> None:
        """Update scan statistics."""
        self.total_items = len(self.movies) + len(self.series)
        self.total_issues = (
            sum(len(movie.issues) for movie in self.movies)
            + sum(len(series.issues) for series in self.series)
            + sum(len(season.issues) for series in self.series for season in series.seasons)
            + sum(
                len(episode.issues)
                for series in self.series
                for season in series.seasons
                for episode in season.episodes
            )
        )

    def get_items_with_issues(self) -> list[MediaItem]:
        """Get all items with validation issues."""
        items: list[MediaItem] = []
        for movie in self.movies:
            if movie.has_issues:
                items.append(movie)

        for series in self.series:
            if series.has_issues:
                items.append(series)
            for season in series.seasons:
                if season.has_issues:
                    items.append(season)
                for episode in season.episodes:
                    if episode.has_issues:
                        items.append(episode)

        return items
