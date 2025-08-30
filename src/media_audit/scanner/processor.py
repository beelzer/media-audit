"""Media processor module for analyzing individual media items."""

from __future__ import annotations

import concurrent.futures
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from media_audit.core import MovieItem, SeriesItem
from media_audit.domain.parsing import MovieParser, TVParser
from media_audit.domain.patterns import MediaPatterns
from media_audit.domain.validation import MediaValidator
from media_audit.infrastructure.cache import MediaCache
from media_audit.shared.logging import get_logger

if TYPE_CHECKING:
    from .config import ScannerConfig


class MediaProcessor:
    """Processes individual media items with validation."""

    def __init__(self, config: ScannerConfig):
        """Initialize processor with configuration."""
        self.config = config
        self.logger = get_logger("processor")

        # Initialize cache
        self.cache = MediaCache(cache_dir=config.cache_dir, enabled=config.cache_enabled)

        # Initialize patterns
        self.patterns = MediaPatterns()
        compiled = self.patterns.compile_patterns()

        # Initialize parsers
        self.movie_parser = MovieParser(compiled, cache=self.cache)
        self.tv_parser = TVParser(compiled, cache=self.cache)

        # Episode progress tracking
        self.episode_progress_callback: Callable[[int, int, str, bool], None] | None = None
        self.current_episode_num = 0
        self.total_episodes = 0

        # Initialize validator
        from media_audit.infrastructure.config import ScanConfig

        scan_config = ScanConfig(
            root_paths=config.root_paths,
            profiles=config.profiles,
            allowed_codecs=self._parse_codecs(config.allowed_codecs),
            concurrent_workers=config.concurrent_workers,
            cache_enabled=config.cache_enabled,
            cache_dir=config.cache_dir,
            patterns=self.patterns,
        )
        self.validator = MediaValidator(scan_config, cache=self.cache)

        # Thread pool for parallel processing
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=min(config.concurrent_workers, 32)
        )

    def process(self, path: Path) -> MovieItem | SeriesItem | None:
        """Process a single media item."""
        try:
            # Track cache hits before processing
            initial_hits = 0
            if self.cache and self.cache.enabled:
                initial_hits = getattr(self.cache, "hits", 0)

            # Determine media type
            result: SeriesItem | MovieItem | None
            if self._is_tv_series(path):
                result = self._process_series(path)
            else:
                result = self._process_movie(path)

            # Check if we had cache hits
            final_hits = 0
            if self.cache and self.cache.enabled:
                final_hits = getattr(self.cache, "hits", 0)
            self.last_was_cache_hit = final_hits > initial_hits

            return result

        except Exception as e:
            self.logger.error(f"Failed to process {path}: {e}")
            self.last_was_cache_hit = False
            return None

    def _is_tv_series(self, path: Path) -> bool:
        """Check if path contains a TV series."""
        # Look for season directories
        for item in path.iterdir():
            if item.is_dir():
                name_lower = item.name.lower()
                if (
                    name_lower.startswith("season")
                    or name_lower.startswith("s0")
                    or name_lower.startswith("s1")
                    or name_lower.startswith("s2")
                    or name_lower == "specials"
                ):
                    return True
        return False

    def _process_movie(self, path: Path) -> MovieItem | None:
        """Process a movie directory."""
        try:
            # Parse movie
            movie = self.movie_parser.parse_sync(path)

            if movie:
                # Run validation
                self._validate_movie_sync(movie)
                self.logger.debug(f"Processed movie: {movie.name}")

            return movie

        except Exception as e:
            self.logger.error(f"Error processing movie {path}: {e}")
            return None

    def set_episode_progress_callback(self, callback: object, total_episodes: int) -> None:
        """Set callback for episode progress updates."""
        self.episode_progress_callback = callback  # type: ignore[assignment]
        self.current_episode_num = 0
        self.total_episodes = total_episodes

        # Create internal callback for the parser
        def parser_callback(episode_name: str, video_path: object, phase: str) -> None:
            if phase == "start":
                # Don't increment on start, just show message
                if self.episode_progress_callback:
                    self.episode_progress_callback(
                        self.current_episode_num, self.total_episodes, episode_name, False
                    )
            elif phase == "complete":
                # Increment counter on completion
                self.current_episode_num += 1
                if self.episode_progress_callback:
                    # Update with completion
                    self.episode_progress_callback(
                        self.current_episode_num, self.total_episodes, episode_name, False
                    )

        self.tv_parser.set_episode_callback(parser_callback)

    def _process_series(self, path: Path) -> SeriesItem | None:
        """Process a TV series directory."""
        try:
            # Parse series
            series = self.tv_parser.parse_sync(path)

            if series:
                # Run validation
                self._validate_series_sync(series)
                self.logger.debug(f"Processed series: {series.name}")

            return series

        except Exception as e:
            self.logger.error(f"Error processing series {path}: {e}")
            return None

    def _validate_movie_sync(self, movie: MovieItem) -> None:
        """Synchronous wrapper for movie validation."""
        import asyncio

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.validator.validate_movie(movie))
        finally:
            loop.close()

    def _validate_series_sync(self, series: SeriesItem) -> None:
        """Synchronous wrapper for series validation."""
        import asyncio

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.validator.validate_series(series))
        finally:
            loop.close()

    def _parse_codecs(self, codec_names: list[str]) -> list[Any]:
        """Parse codec names to enum values."""
        from media_audit.core import CodecType

        codecs = []
        for name in codec_names:
            try:
                codec = CodecType[name.upper()]
                codecs.append(codec)
            except KeyError:
                self.logger.warning(f"Unknown codec: {name}")

        return codecs

    def shutdown(self) -> None:
        """Shutdown the processor and cleanup resources."""
        self.executor.shutdown(wait=True)
