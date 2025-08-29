"""Core domain models for media audit using Python 3.13 features."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, override

from .enums import CodecType, MediaType, ValidationStatus

# Type aliases using Python 3.10+ syntax
type Resolution = tuple[int, int]
type PathLike = Path | str

# Resolution constants
RESOLUTION_4K = (3840, 2160)
RESOLUTION_1080P = (1920, 1080)
RESOLUTION_720P = (1280, 720)

# Bitrate thresholds (in bits per second)
BITRATE_1080P_MIN = 5_000_000  # 5 Mbps minimum for good quality 1080p
BITRATE_4K_MIN = 15_000_000  # 15 Mbps minimum for good quality 4K


@dataclass(slots=True, frozen=False)
class ValidationIssue:
    """Represents a validation issue found during scanning.

    Using slots for better memory efficiency in Python 3.10+.
    """

    category: str
    message: str
    severity: ValidationStatus
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category,
            "message": self.message,
            "severity": self.severity.value,
            "details": self.details,
        }


@dataclass(slots=True)
class VideoInfo:
    """Information about a video file using slots for efficiency."""

    path: Path
    codec: CodecType | None = None
    resolution: Resolution | None = None
    duration: float | None = None
    bitrate: int | None = None
    size: int = 0
    frame_rate: float | None = None
    audio_codec: str | None = None
    audio_channels: int | None = None
    audio_bitrate: int | None = None
    raw_info: dict[str, Any] = field(default_factory=dict)

    @property
    def is_high_quality(self) -> bool:
        """Check if video is high quality using modern comparisons."""
        if not self.resolution:
            return False

        width, height = self.resolution
        # Using match/case for quality assessment
        match (width, height):
            case (w, h) if w >= RESOLUTION_4K[0] and h >= RESOLUTION_4K[1]:  # 4K
                return True
            case (w, h) if w >= RESOLUTION_1080P[0] and h >= RESOLUTION_1080P[1]:  # Full HD
                return bool(self.bitrate and self.bitrate >= BITRATE_1080P_MIN)
            case _:
                return False


@dataclass(slots=True)
class MediaAssets:
    """Collection of media assets using slots."""

    posters: list[Path] = field(default_factory=list)
    backgrounds: list[Path] = field(default_factory=list)
    banners: list[Path] = field(default_factory=list)
    logos: list[Path] = field(default_factory=list)
    trailers: list[Path] = field(default_factory=list)
    title_cards: list[Path] = field(default_factory=list)
    subtitles: list[Path] = field(default_factory=list)
    nfo_files: list[Path] = field(default_factory=list)

    def has_minimal_assets(self) -> bool:
        """Check if minimal assets are present."""
        return bool(self.posters or self.nfo_files)

    def all_assets(self) -> list[Path]:
        """Get all assets as a flat list."""
        return [
            *self.posters,
            *self.backgrounds,
            *self.banners,
            *self.logos,
            *self.trailers,
            *self.title_cards,
            *self.subtitles,
            *self.nfo_files,
        ]


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
        """Get overall validation status using any() with generator."""
        # Using generator expressions for efficiency
        if any(issue.severity == ValidationStatus.ERROR for issue in self.issues):
            return ValidationStatus.ERROR
        if any(issue.severity == ValidationStatus.WARNING for issue in self.issues):
            return ValidationStatus.WARNING
        return ValidationStatus.VALID

    @property
    def has_issues(self) -> bool:
        """Check if item has any validation issues."""
        return len(self.issues) > 0

    def add_issue(
        self,
        category: str,
        message: str,
        severity: ValidationStatus = ValidationStatus.WARNING,
        **details: Any,
    ) -> None:
        """Add a validation issue with kwargs for details."""
        self.issues.append(
            ValidationIssue(
                category=category,
                message=message,
                severity=severity,
                details=details,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": str(self.path),
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "issues": [issue.to_dict() for issue in self.issues],
            "metadata": self.metadata,
        }


@dataclass
class MovieItem(MediaItem):
    """Represents a movie in the media library."""

    year: int | None = None
    imdb_id: str | None = None
    tmdb_id: str | None = None
    quality: str | None = None
    source: str | None = None
    release_group: str | None = None
    codec: CodecType | None = None
    resolution: str | None = None
    size_gb: float | None = None
    duration_mins: int | None = None
    bitrate: int | None = None
    audio_codec: str | None = None
    audio_channels: str | None = None
    has_subtitles: bool = False
    video_info: VideoInfo | None = None

    def __post_init__(self) -> None:
        """Initialize movie-specific attributes."""
        if self.type != MediaType.MOVIE:
            self.type = MediaType.MOVIE

    @override
    def to_dict(self) -> dict[str, Any]:
        """Convert movie to dictionary."""
        data = super().to_dict()
        data.update(
            {
                "year": self.year,
                "codec": self.codec.value if self.codec else None,
                "resolution": self.resolution,
                "size_gb": self.size_gb,
                "duration_mins": self.duration_mins,
            }
        )
        return data


@dataclass
class EpisodeItem(MediaItem):
    """Represents a single TV episode."""

    season_number: int = 0
    episode_number: int = 0
    title: str | None = None
    air_date: datetime | None = None
    duration_mins: int | None = None
    codec: CodecType | None = None
    resolution: str | None = None
    size_gb: float | None = None
    video_info: VideoInfo | None = None

    def __post_init__(self) -> None:
        """Initialize episode-specific attributes."""
        if self.type != MediaType.TV_EPISODE:
            self.type = MediaType.TV_EPISODE

    @override
    def to_dict(self) -> dict[str, Any]:
        """Convert episode to dictionary."""
        data = super().to_dict()
        data.update(
            {
                "season_number": self.season_number,
                "episode_number": self.episode_number,
                "title": self.title,
                "air_date": self.air_date.isoformat() if self.air_date else None,
                "duration_mins": self.duration_mins,
                "codec": self.codec.value if self.codec else None,
                "resolution": self.resolution,
                "size_gb": self.size_gb,
            }
        )
        return data


@dataclass
class SeasonItem(MediaItem):
    """Represents a TV season."""

    series_name: str = ""
    season_number: int = 0
    episodes: list[EpisodeItem] = field(default_factory=list)
    year: int | None = None

    def __post_init__(self) -> None:
        """Initialize season-specific attributes."""
        if self.type != MediaType.TV_SEASON:
            self.type = MediaType.TV_SEASON

    @property
    def episode_count(self) -> int:
        """Get the number of episodes."""
        return len(self.episodes)

    @property
    def total_size_gb(self) -> float:
        """Calculate total size of all episodes."""
        return sum(ep.size_gb or 0 for ep in self.episodes)

    @override
    def to_dict(self) -> dict[str, Any]:
        """Convert season to dictionary."""
        data = super().to_dict()
        data.update(
            {
                "series_name": self.series_name,
                "season_number": self.season_number,
                "episode_count": self.episode_count,
                "episodes": [ep.to_dict() for ep in self.episodes],
                "year": self.year,
                "total_size_gb": self.total_size_gb,
            }
        )
        return data


@dataclass
class SeriesItem(MediaItem):
    """Represents a complete TV series."""

    seasons: list[SeasonItem] = field(default_factory=list)
    imdb_id: str | None = None
    tmdb_id: str | None = None
    tvdb_id: str | None = None
    year_started: int | None = None
    year_ended: int | None = None
    total_episodes: int | None = None

    def __post_init__(self) -> None:
        """Initialize series-specific attributes."""
        if self.type != MediaType.TV_SERIES:
            self.type = MediaType.TV_SERIES

    @property
    def season_count(self) -> int:
        """Get the number of seasons."""
        return len(self.seasons)

    @property
    def actual_episode_count(self) -> int:
        """Count actual episodes across all seasons."""
        return sum(season.episode_count for season in self.seasons)

    @property
    def total_size_gb(self) -> float:
        """Calculate total size across all seasons."""
        return sum(season.total_size_gb for season in self.seasons)

    @override
    def to_dict(self) -> dict[str, Any]:
        """Convert series to dictionary."""
        data = super().to_dict()
        data.update(
            {
                "season_count": self.season_count,
                "seasons": [season.to_dict() for season in self.seasons],
                "imdb_id": self.imdb_id,
                "year_started": self.year_started,
                "year_ended": self.year_ended,
                "total_episodes": self.total_episodes,
                "actual_episode_count": self.actual_episode_count,
                "total_size_gb": self.total_size_gb,
            }
        )
        return data


@dataclass
class ScanResult:
    """Results from a media library scan."""

    scan_time: datetime
    duration: float
    root_paths: list[Path]
    movies: list[MovieItem] = field(default_factory=list)
    series: list[SeriesItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total_items: int = 0
    total_issues: int = 0

    def update_stats(self) -> None:
        """Update calculated statistics."""
        self.total_items = len(self.movies) + len(self.series)

        # Count all issues
        self.total_issues = sum(len(movie.issues) for movie in self.movies)
        self.total_issues += sum(len(series.issues) for series in self.series)

        # Count season and episode issues
        for series in self.series:
            for season in series.seasons:
                self.total_issues += len(season.issues)
                for episode in season.episodes:
                    self.total_issues += len(episode.issues)

    def get_items_with_issues(self) -> list[MediaItem]:
        """Get all items that have validation issues."""
        items: list[MediaItem] = []

        # Add movies with issues
        items.extend(movie for movie in self.movies if movie.has_issues)

        # Add series with issues
        items.extend(series for series in self.series if series.has_issues)

        # Add seasons and episodes with issues
        for series in self.series:
            items.extend(season for season in series.seasons if season.has_issues)
            for season in series.seasons:
                items.extend(episode for episode in season.episodes if episode.has_issues)

        return items

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "scan_time": self.scan_time.isoformat(),
            "duration": self.duration,
            "root_paths": [str(p) for p in self.root_paths],
            "total_items": self.total_items,
            "total_issues": self.total_issues,
            "movies": [movie.to_dict() for movie in self.movies],
            "series": [series.to_dict() for series in self.series],
            "errors": self.errors,
        }
