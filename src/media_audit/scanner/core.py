"""Core scanner implementation with improved architecture."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from media_audit.shared.logging import get_logger

if TYPE_CHECKING:
    from .config import ScannerConfig
    from .results import ScanResults


class Scanner:
    """Main scanner class with clean separation of concerns."""

    def __init__(self, config: ScannerConfig):
        """Initialize scanner with configuration."""
        self.config = config
        self.logger = get_logger("scanner")
        self._start_time = 0.0

        # Initialize components lazily
        self._discovery = None
        self._processor = None
        self._progress = None
        self._results = None

    @property
    def discovery(self):
        """Lazy-load path discovery component."""
        if self._discovery is None:
            from .discovery import PathDiscovery

            self._discovery = PathDiscovery(self.config)
        return self._discovery

    @property
    def processor(self):
        """Lazy-load media processor component."""
        if self._processor is None:
            from .processor import MediaProcessor

            self._processor = MediaProcessor(self.config)
        return self._processor

    @property
    def progress(self):
        """Lazy-load progress tracker component."""
        if self._progress is None:
            from .progress_multi import ProgressTracker

            self._progress = ProgressTracker(self.config)
        return self._progress

    @property
    def results(self):
        """Lazy-load results container."""
        if self._results is None:
            from .results import ScanResults

            self._results = ScanResults()
        return self._results

    def scan(self) -> ScanResults:
        """Execute the scan with proper progress tracking."""
        self._start_time = time.time()

        try:
            # Initialize progress tracking
            self.progress.start()

            # Phase 1: Discovery
            self.logger.info("Starting media discovery phase")
            paths_by_root = self._discover_media()

            if not paths_by_root:
                self.logger.warning("No media items found to scan")
                return self.results

            # Phase 2: Processing
            total_items = sum(len(paths) for paths in paths_by_root.values())
            self.logger.info(f"Processing {total_items} media items")
            self.progress.setup_processing(total_items)
            self._process_media_by_root(paths_by_root)

            # Phase 3: Finalization
            self._finalize_results()

            return self.results

        except KeyboardInterrupt:
            self.logger.info("Scan interrupted by user")
            self.progress.cancel()
            self.results.mark_cancelled()
            return self.results

        except Exception as e:
            self.logger.error(f"Scan failed: {e}", exc_info=True)
            self.results.add_error(str(e))
            raise

        finally:
            self.progress.stop()

    def _discover_media(self) -> dict[Path, list[Path]]:
        """Discover all media paths to process, organized by root."""
        paths_by_root = {}
        total_count = 0

        for root_path in self.config.root_paths:
            if not root_path.exists():
                self.logger.warning(f"Root path does not exist: {root_path}")
                self.results.add_error(f"Path not found: {root_path}")
                continue

            # Format root path for display
            display_path = (
                root_path.name if root_path.parent.name.lower() == "media" else str(root_path)
            )
            self.progress.update_discovery(f"Scanning {display_path}")
            paths = self.discovery.discover(root_path)

            if paths:
                paths_by_root[root_path] = paths
                total_count += len(paths)
                # Setup progress bar for this root
                self.progress.setup_root_processing(root_path, len(paths))

        self.logger.info(f"Discovered {total_count} media items across {len(paths_by_root)} roots")
        return paths_by_root

    def _process_media_by_root(self, paths_by_root: dict[Path, list[Path]]) -> None:
        """Process media items organized by root path."""
        overall_idx = 0
        total_items = sum(len(paths) for paths in paths_by_root.values())

        # Track cache stats before processing
        if self.processor.cache and self.processor.cache.enabled:
            getattr(self.processor.cache, "hits", 0)

        for root_path, media_paths in paths_by_root.items():
            # Set current root for progress tracking
            self.progress.set_current_root(root_path)

            # Track cache hits for this root
            if self.processor.cache and self.processor.cache.enabled:
                getattr(self.processor.cache, "hits", 0)

            for path in media_paths:
                if self.progress.is_cancelled():
                    break

                # Show what we're about to process (message on start)
                self.progress.update_processing(overall_idx, total_items, path.name)

                # Check if this is a TV series and show episode progress
                is_tv_series = self._is_tv_series_path(path)
                if is_tv_series:
                    episode_count = self._count_episodes(path)
                    if episode_count > 0:
                        # Show episode progress bar
                        self.progress.start_series_scan(path.name, episode_count)
                        # Process with episode tracking
                        media_item = self._process_series_with_progress(path, episode_count)
                        # Remove the progress bar
                        self.progress.end_series_scan()
                    else:
                        # No episodes found, process normally
                        media_item = self.processor.process(path)
                else:
                    # Process non-TV content normally
                    media_item = self.processor.process(path)

                if media_item:
                    self.results.add_item(media_item)

                # Check if this was a cache hit
                if (
                    hasattr(self.processor, "last_was_cache_hit")
                    and self.processor.last_was_cache_hit
                ):
                    self.progress.add_cache_hit(root_path)

                # Increment progress AFTER processing is complete
                overall_idx += 1
                self.progress.advance_processing(overall_idx, total_items)

            if self.progress.is_cancelled():
                break

    def _is_tv_series_path(self, path: Path) -> bool:
        """Check if a path is a TV series."""
        # Check for season directories
        if not path.is_dir():
            return False

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

    def _count_episodes(self, path: Path) -> int:
        """Count total episodes in a TV series."""
        count = 0
        video_extensions = {".mkv", ".mp4", ".avi", ".m4v", ".ts", ".m2ts"}

        for season_dir in path.iterdir():
            if season_dir.is_dir():
                name_lower = season_dir.name.lower()
                if (
                    name_lower.startswith("season")
                    or name_lower.startswith("s0")
                    or name_lower.startswith("s1")
                    or name_lower.startswith("s2")
                    or name_lower == "specials"
                ):
                    # Count video files in this season
                    for file in season_dir.iterdir():
                        if file.is_file() and file.suffix.lower() in video_extensions:
                            count += 1
        return count

    def _process_series_with_progress(self, path: Path, episode_count: int) -> Any:
        """Process a TV series with episode progress tracking."""
        # Set up the callback to update progress
        self.processor.set_episode_progress_callback(
            lambda num, total, name, cached: self.progress.update_episode_scan(
                num, total, name, cached
            ),
            episode_count,
        )

        # Process the series (this will trigger callbacks for each episode)
        result = self.processor.process(path)

        # Clear the callback
        self.processor.set_episode_progress_callback(None, 0)

        return result

    def _finalize_results(self) -> None:
        """Finalize scan results."""
        duration = time.time() - self._start_time
        self.results.finalize(duration)

        self.logger.info(
            f"Scan completed in {duration:.2f}s - "
            f"Found {self.results.total_items} items with {self.results.total_issues} issues"
        )
