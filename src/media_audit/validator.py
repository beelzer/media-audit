"""Media validation logic."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .logging import get_logger
from .models import (
    CodecType,
    EpisodeItem,
    MediaItem,
    MovieItem,
    SeasonItem,
    SeriesItem,
    ValidationIssue,
    ValidationStatus,
    VideoInfo,
)
from .probe import probe_video

if TYPE_CHECKING:
    from .config import ScanConfig


class MediaValidator:
    """Validates media items against configured rules."""

    def __init__(self, config: ScanConfig, cache: Any = None) -> None:
        """Initialize validator with configuration."""
        self.config = config
        self.allowed_codecs = set(config.allowed_codecs)
        self.cache = cache
        self.logger = get_logger("validator")

    def validate(self, item: MediaItem) -> None:
        """Validate a media item and add issues."""
        if isinstance(item, MovieItem):
            self.validate_movie(item)
        elif isinstance(item, SeriesItem):
            self.validate_series(item)
        elif isinstance(item, SeasonItem):
            self.validate_season(item)
        elif isinstance(item, EpisodeItem):
            self.validate_episode(item)

    def validate_movie(self, movie: MovieItem) -> None:
        """Validate a movie."""
        self.logger.debug(f"Validating movie: {movie.name}")
        # Check for required assets
        if not movie.assets.posters:
            movie.issues.append(
                ValidationIssue(
                    category="assets",
                    message="Missing poster image",
                    severity=ValidationStatus.ERROR,
                    details={"expected": ["poster.jpg", "folder.jpg", "movie.jpg"]},
                )
            )

        if not movie.assets.backgrounds:
            movie.issues.append(
                ValidationIssue(
                    category="assets",
                    message="Missing background/fanart image",
                    severity=ValidationStatus.ERROR,
                    details={"expected": ["fanart.jpg", "background.jpg", "backdrop.jpg"]},
                )
            )

        if not movie.assets.trailers and not self._has_trailer_folder(movie.path):
            movie.issues.append(
                ValidationIssue(
                    category="assets",
                    message="Missing trailer",
                    severity=ValidationStatus.WARNING,
                    details={"expected": ["*-trailer.mp4", "Trailers/"]},
                )
            )

        # Check video encoding
        if movie.video_info:
            self._validate_video_encoding(movie, movie.video_info)
        else:
            movie.issues.append(
                ValidationIssue(
                    category="video",
                    message="No video file found",
                    severity=ValidationStatus.ERROR,
                )
            )

    def validate_series(self, series: SeriesItem) -> None:
        """Validate a TV series."""
        self.logger.debug(f"Validating series: {series.name}")
        # Check for series-level assets
        if not series.assets.posters:
            series.issues.append(
                ValidationIssue(
                    category="assets",
                    message="Missing series poster",
                    severity=ValidationStatus.ERROR,
                    details={"expected": ["poster.jpg", "folder.jpg"]},
                )
            )

        if not series.assets.backgrounds:
            series.issues.append(
                ValidationIssue(
                    category="assets",
                    message="Missing series background/fanart",
                    severity=ValidationStatus.ERROR,
                    details={"expected": ["fanart.jpg", "background.jpg"]},
                )
            )

        # Banner is optional
        if not series.assets.banners:
            series.issues.append(
                ValidationIssue(
                    category="assets",
                    message="Missing series banner (optional)",
                    severity=ValidationStatus.WARNING,
                    details={"expected": ["banner.jpg"]},
                )
            )

        # Validate seasons
        for season in series.seasons:
            self.validate_season(season)

    def validate_season(self, season: SeasonItem) -> None:
        """Validate a TV season."""
        # Check for season poster
        if not season.assets.posters:
            season.issues.append(
                ValidationIssue(
                    category="assets",
                    message=f"Missing poster for Season {season.season_number}",
                    severity=ValidationStatus.WARNING,
                    details={"expected": [f"Season{season.season_number:02d}.jpg"]},
                )
            )

        # Validate episodes
        for episode in season.episodes:
            self.validate_episode(episode)

    def validate_episode(self, episode: EpisodeItem) -> None:
        """Validate a TV episode."""
        # Check for title card
        if not episode.assets.title_cards:
            episode.issues.append(
                ValidationIssue(
                    category="assets",
                    message=f"Missing title card for S{episode.season_number:02d}E{episode.episode_number:02d}",
                    severity=ValidationStatus.WARNING,
                    details={
                        "expected": [
                            f"S{episode.season_number:02d}E{episode.episode_number:02d}.jpg"
                        ]
                    },
                )
            )

        # Check video encoding
        if episode.video_info:
            self._validate_video_encoding(episode, episode.video_info)
        else:
            episode.issues.append(
                ValidationIssue(
                    category="video",
                    message="No video file found for episode",
                    severity=ValidationStatus.ERROR,
                )
            )

    def _validate_video_encoding(self, item: MediaItem, video_info: VideoInfo) -> None:
        """Validate video encoding."""
        # Probe video if not already done
        if video_info.codec is None:
            try:
                probed_info = probe_video(video_info.path, cache=self.cache)
                video_info.codec = probed_info.codec
                video_info.resolution = probed_info.resolution
                video_info.duration = probed_info.duration
                video_info.bitrate = probed_info.bitrate
                video_info.size = probed_info.size
                video_info.raw_info = probed_info.raw_info
            except Exception as e:
                self.logger.error(f"Failed to probe video file {video_info.path}: {e}")
                item.issues.append(
                    ValidationIssue(
                        category="video",
                        message=f"Failed to probe video file: {e}",
                        severity=ValidationStatus.ERROR,
                        details={"file": str(video_info.path)},
                    )
                )
                return

        # Check codec
        if video_info.codec and video_info.codec not in self.allowed_codecs:
            item.issues.append(
                ValidationIssue(
                    category="encoding",
                    message=f"Video uses non-preferred codec: {video_info.codec.value}",
                    severity=ValidationStatus.WARNING,
                    details={
                        "codec": video_info.codec.value,
                        "allowed": [c.value for c in self.allowed_codecs],
                        "file": video_info.path.name,
                    },
                )
            )

            # Special warning for H.264
            if video_info.codec == CodecType.H264:
                item.issues.append(
                    ValidationIssue(
                        category="encoding",
                        message="Consider re-encoding from H.264 to HEVC/AV1 for better compression",
                        severity=ValidationStatus.WARNING,
                        details={"file": video_info.path.name},
                    )
                )

    def _has_trailer_folder(self, path: Path) -> bool:
        """Check if path has a Trailers folder."""
        trailer_folder = path / "Trailers"
        if trailer_folder.exists() and trailer_folder.is_dir():
            # Check if it contains video files
            for file in trailer_folder.iterdir():
                if file.suffix.lower() in {".mp4", ".mkv", ".mov", ".avi"}:
                    return True
        return False
