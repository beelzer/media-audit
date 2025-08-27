"""Data models for media audit results using Python 3.13 features."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, override

# Type aliases using Python 3.10+ syntax
type Resolution = tuple[int, int]
type PathLike = Path | str


class MediaType(StrEnum):
    """Type of media content using StrEnum for better string handling."""

    MOVIE = "movie"
    TV_SERIES = "tv_series"
    TV_SEASON = "tv_season"
    TV_EPISODE = "tv_episode"
    UNKNOWN = "unknown"

    @override
    def __str__(self) -> str:
        """Return readable string representation."""
        return self.value.replace("_", " ").title()


class ValidationStatus(StrEnum):
    """Validation status for media items."""

    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"


class CodecType(StrEnum):
    """Video codec types using StrEnum."""

    HEVC = "hevc"
    AV1 = "av1"
    H264 = "h264"
    H265 = "h265"
    VP9 = "vp9"
    VP8 = "vp8"
    MPEG4 = "mpeg4"
    MPEG2 = "mpeg2"
    XVID = "xvid"
    DIVX = "divx"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, codec_str: str) -> CodecType:
        """Create CodecType from string using match/case."""
        if not codec_str:
            return cls.UNKNOWN

        codec_lower = codec_str.lower().strip()

        # Using match/case for cleaner codec mapping
        match codec_lower:
            case "hevc" | "h265" | "x265":
                return cls.HEVC
            case "h264" | "x264" | "avc":
                return cls.H264
            case "av1" | "av01":
                return cls.AV1
            case "vp9":
                return cls.VP9
            case "vp8":
                return cls.VP8
            case "mpeg4" | "mp4v":
                return cls.MPEG4
            case "mpeg2" | "mp2v":
                return cls.MPEG2
            case "xvid":
                return cls.XVID
            case "divx":
                return cls.DIVX
            case _:
                return cls.UNKNOWN


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
            case (w, h) if w >= 3840 and h >= 2160:  # 4K
                return True
            case (w, h) if w >= 1920 and h >= 1080:  # Full HD
                return bool(self.bitrate and self.bitrate >= 5_000_000)
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
    """Represents a movie."""

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
                "bitrate": self.bitrate,
                "audio_codec": self.audio_codec,
                "audio_channels": self.audio_channels,
                "has_subtitles": self.has_subtitles,
            }
        )
        return data


@dataclass
class EpisodeItem(MediaItem):
    """Represents a TV episode."""

    season_number: int | None = None
    episode_number: int | None = None
    episode_title: str | None = None
    quality: str | None = None
    source: str | None = None
    release_group: str | None = None
    codec: CodecType | None = None
    resolution: str | None = None
    size_gb: float | None = None
    duration_mins: int | None = None
    video_info: VideoInfo | None = None

    def __post_init__(self) -> None:
        """Initialize episode-specific attributes."""
        if self.type != MediaType.TV_EPISODE:
            self.type = MediaType.TV_EPISODE

    @property
    def episode_code(self) -> str:
        """Get episode code like S01E01."""
        if self.season_number is not None and self.episode_number is not None:
            return f"S{self.season_number:02d}E{self.episode_number:02d}"
        return "Unknown"

    @override
    def to_dict(self) -> dict[str, Any]:
        """Convert episode to dictionary."""
        data = super().to_dict()
        data.update(
            {
                "season_number": self.season_number,
                "episode_number": self.episode_number,
                "episode_code": self.episode_code,
                "codec": self.codec.value if self.codec else None,
                "resolution": self.resolution,
                "size_gb": self.size_gb,
                "duration_mins": self.duration_mins,
            }
        )
        return data


@dataclass
class SeasonItem(MediaItem):
    """Represents a TV season."""

    season_number: int | None = None
    episodes: list[EpisodeItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize season-specific attributes."""
        if self.type != MediaType.TV_SEASON:
            self.type = MediaType.TV_SEASON

    @property
    def episode_count(self) -> int:
        """Get number of episodes in season."""
        return len(self.episodes)

    @property
    def status(self) -> ValidationStatus:
        """Get overall status including episode statuses."""
        # Check own issues first
        own_status = super().status

        # Check episode statuses
        if self.episodes:
            episode_statuses = [ep.status for ep in self.episodes]
            if ValidationStatus.ERROR in episode_statuses:
                return ValidationStatus.ERROR
            if (
                ValidationStatus.WARNING in episode_statuses
                and own_status != ValidationStatus.ERROR
            ):
                return ValidationStatus.WARNING

        return own_status

    @override
    def to_dict(self) -> dict[str, Any]:
        """Convert season to dictionary."""
        data = super().to_dict()
        data.update(
            {
                "season_number": self.season_number,
                "episode_count": self.episode_count,
                "episodes": [ep.to_dict() for ep in self.episodes],
            }
        )
        return data


@dataclass
class SeriesItem(MediaItem):
    """Represents a TV series."""

    seasons: list[SeasonItem] = field(default_factory=list)
    imdb_id: str | None = None
    tvdb_id: str | None = None
    tmdb_id: str | None = None
    total_episodes: int = 0
    expected_episodes: int | None = None
    missing_episodes: list[str] = field(default_factory=list)
    codec: CodecType | None = None
    mixed_codecs: bool = False
    codec_list: list[CodecType] = field(default_factory=list)
    resolution: str | None = None
    min_episode_resolution: str | None = None
    total_size_gb: float | None = None

    def __post_init__(self) -> None:
        """Initialize series-specific attributes."""
        if self.type != MediaType.TV_SERIES:
            self.type = MediaType.TV_SERIES

    def update_episode_count(self) -> None:
        """Update total episode count from seasons."""
        self.total_episodes = sum(season.episode_count for season in self.seasons)

    @property
    def season_count(self) -> int:
        """Get number of seasons."""
        return len(self.seasons)

    @property
    def status(self) -> ValidationStatus:
        """Get overall status including season statuses."""
        # Check own issues first
        own_status = super().status

        # Check season statuses
        if self.seasons:
            season_statuses = [season.status for season in self.seasons]
            if ValidationStatus.ERROR in season_statuses:
                return ValidationStatus.ERROR
            if ValidationStatus.WARNING in season_statuses and own_status != ValidationStatus.ERROR:
                return ValidationStatus.WARNING

        return own_status

    @override
    def to_dict(self) -> dict[str, Any]:
        """Convert series to dictionary."""
        data = super().to_dict()
        data.update(
            {
                "season_count": self.season_count,
                "total_episodes": self.total_episodes,
                "expected_episodes": self.expected_episodes,
                "missing_episodes": self.missing_episodes,
                "seasons": [season.to_dict() for season in self.seasons],
                "codec": self.codec.value if self.codec else None,
                "mixed_codecs": self.mixed_codecs,
                "resolution": self.resolution,
                "total_size_gb": self.total_size_gb,
            }
        )
        return data


@dataclass
class ScanResult:
    """Results from a media library scan."""

    scan_time: datetime | None
    duration: float
    root_paths: list[Path]
    movies: list[MovieItem] = field(default_factory=list)
    series: list[SeriesItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total_items: int = 0
    total_issues: int = 0

    def update_stats(self) -> None:
        """Update statistics using list comprehensions."""
        self.total_items = len(self.movies) + len(self.series)

        # Using nested comprehensions for issue counting
        self.total_issues = sum([len(item.issues) for item in [*self.movies, *self.series]])

        # Add season and episode issues
        for series in self.series:
            for season in series.seasons:
                self.total_issues += len(season.issues)
                self.total_issues += sum(len(ep.issues) for ep in season.episodes)

    def get_items_with_issues(self) -> list[MediaItem]:
        """Get all items that have validation issues."""
        items_with_issues: list[MediaItem] = []

        # Use list comprehension with filtering
        items_with_issues.extend([item for item in self.movies if item.has_issues])

        # Add series and their children with issues
        for series in self.series:
            if series.has_issues:
                items_with_issues.append(series)

            for season in series.seasons:
                if season.has_issues:
                    items_with_issues.append(season)

                items_with_issues.extend([ep for ep in season.episodes if ep.has_issues])

        return items_with_issues

    def to_dict(self) -> dict[str, Any]:
        """Convert scan result to dictionary."""
        return {
            "scan_time": self.scan_time.isoformat() if self.scan_time else None,
            "duration": self.duration,
            "root_paths": [str(path) for path in self.root_paths],
            "movies": [movie.to_dict() for movie in self.movies],
            "series": [series.to_dict() for series in self.series],
            "errors": self.errors,
            "stats": {
                "total_items": self.total_items,
                "total_issues": self.total_issues,
                "movie_count": len(self.movies),
                "series_count": len(self.series),
            },
        }
