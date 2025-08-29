"""Media validation logic.

Provides comprehensive validation for media items, checking for missing assets,
encoding issues, and structural problems. Integrates with the scanning pipeline
to identify and categorize issues.

Validation Categories:
    - Assets: Missing artwork, trailers, subtitles
    - Encoding: Non-optimal codecs, resolution issues
    - Structure: Missing episodes, naming problems
    - Metadata: Missing or incorrect metadata

Example:
    >>> from media_audit.domain.validation import MediaValidator
    >>> from media_audit.infrastructure.config import ScanConfig
    >>>
    >>> config = ScanConfig(allowed_codecs=[CodecType.HEVC, CodecType.AV1])
    >>> validator = MediaValidator(config)
    >>> validator.validate(movie_item)
    >>> print(f"Found {len(movie_item.issues)} issues")

"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from media_audit.core import (
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
from media_audit.infrastructure.cache import MediaCache
from media_audit.infrastructure.probe import probe_video, probe_video_async

if TYPE_CHECKING:
    from media_audit.infrastructure.config import ScanConfig
from media_audit.shared.logging import get_logger


class MediaValidator:
    """Validates media items against configured rules.

    Applies validation rules based on configuration to identify issues
    with media files, organization, and metadata.

    Attributes:
        config: Scan configuration with validation rules
        allowed_codecs: Set of acceptable video codecs
        cache: Optional cache for probe results
        logger: Logger for debug output

    """

    def __init__(self, config: ScanConfig, cache: MediaCache | None = None) -> None:
        """Initialize validator with configuration.

        Args:
            config: Scan configuration with validation rules
            cache: Optional MediaCache instance for probe caching

        """
        self.config = config
        self.allowed_codecs = set(config.allowed_codecs)
        self.cache = cache
        self.logger = get_logger("validator")

    def validate(self, item: MediaItem) -> None:
        """Validate a media item and add issues.

        Dispatches to appropriate validation method based on item type.
        Issues are added directly to the item's issues list.

        Args:
            item: Media item to validate (movie, series, season, or episode)

        """
        if isinstance(item, MovieItem):
            self.validate_movie(item)
        elif isinstance(item, SeriesItem):
            self.validate_series(item)
        elif isinstance(item, SeasonItem):
            self.validate_season(item)
        elif isinstance(item, EpisodeItem):
            self.validate_episode(item)

    async def validate_movie_async(self, movie: MovieItem) -> None:
        """Asynchronously validate a movie for required assets and encoding.

        Checks for:
        - Poster and background images
        - Trailer files
        - Video encoding compliance
        - File presence

        Args:
            movie: Movie item to validate

        """
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
            await self._validate_video_encoding_async(movie, movie.video_info)
        else:
            movie.issues.append(
                ValidationIssue(
                    category="video",
                    message="No video file found",
                    severity=ValidationStatus.ERROR,
                )
            )

    def validate_movie(self, movie: MovieItem) -> None:
        """Validate a movie for required assets and encoding.

        Checks for:
        - Poster and background images
        - Trailer files
        - Video encoding compliance
        - File presence

        Args:
            movie: Movie item to validate

        """
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

    async def validate_series_async(self, series: SeriesItem) -> None:
        """Asynchronously validate a TV series and all its seasons.

        Checks for:
        - Series-level artwork (poster, background, banner)
        - Recursively validates all seasons

        Args:
            series: Series item to validate

        """
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

        # Validate seasons concurrently
        season_tasks = [self.validate_season_async(season) for season in series.seasons]
        await asyncio.gather(*season_tasks)

    def validate_series(self, series: SeriesItem) -> None:
        """Validate a TV series and all its seasons.

        Checks for:
        - Series-level artwork (poster, background, banner)
        - Recursively validates all seasons

        Args:
            series: Series item to validate

        """
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

    async def validate_season_async(self, season: SeasonItem) -> None:
        """Asynchronously validate a TV season and all its episodes.

        Checks for:
        - Season poster
        - Recursively validates all episodes

        Args:
            season: Season item to validate

        """
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

        # Validate episodes concurrently
        episode_tasks = [self.validate_episode_async(episode) for episode in season.episodes]
        await asyncio.gather(*episode_tasks)

    def validate_season(self, season: SeasonItem) -> None:
        """Validate a TV season and all its episodes.

        Checks for:
        - Season poster
        - Recursively validates all episodes

        Args:
            season: Season item to validate

        """
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

    async def validate_episode_async(self, episode: EpisodeItem) -> None:
        """Asynchronously validate a TV episode.

        Checks for:
        - Title card/thumbnail
        - Video file presence
        - Video encoding compliance

        Args:
            episode: Episode item to validate

        """
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
            await self._validate_video_encoding_async(episode, episode.video_info)
        else:
            episode.issues.append(
                ValidationIssue(
                    category="video",
                    message=f"No video file for S{episode.season_number:02d}E{episode.episode_number:02d}",
                    severity=ValidationStatus.ERROR,
                )
            )

    def validate_episode(self, episode: EpisodeItem) -> None:
        """Validate a TV episode.

        Checks for:
        - Title card/thumbnail
        - Video file presence
        - Video encoding compliance

        Args:
            episode: Episode item to validate

        """
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

    async def _validate_video_encoding_async(self, item: MediaItem, video_info: VideoInfo) -> None:
        """Asynchronously validate video encoding against configured rules.

        Probes video file if needed and checks codec compliance.
        Adds warnings for legacy codecs and suggestions for re-encoding.

        Args:
            item: Media item containing the video
            video_info: Video information to validate

        """
        # Probe video if not already done
        if video_info.codec is None:
            try:
                probed_info = await probe_video_async(video_info.path, cache=self.cache)
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

    def _validate_video_encoding(self, item: MediaItem, video_info: VideoInfo) -> None:
        """Validate video encoding against configured rules.

        Probes video file if needed and checks codec compliance.
        Adds warnings for legacy codecs and suggestions for re-encoding.

        Args:
            item: Media item containing the video
            video_info: Video information to validate

        """
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
        """Check if path has a Trailers folder with video files.

        Args:
            path: Directory to check

        Returns:
            bool: True if Trailers folder exists with video files

        """
        trailer_folder = path / "Trailers"
        if trailer_folder.exists() and trailer_folder.is_dir():
            # Check if it contains video files
            for file in trailer_folder.iterdir():
                if file.suffix.lower() in {".mp4", ".mkv", ".mov", ".avi"}:
                    return True
        return False
