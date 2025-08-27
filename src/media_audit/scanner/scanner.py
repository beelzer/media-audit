"""Main media scanner implementation.

This module provides the core scanning functionality for media libraries,
including parallel processing, progress tracking, and cancellation support.
Integrates with parsers and validators to build a complete picture of the
media library's structure and health.

Key Features:
    - Concurrent scanning with configurable worker threads
    - Real-time progress tracking with Rich console output
    - ESC key cancellation support
    - Automatic media type detection
    - Integrated caching for performance

Example:
    >>> from media_audit.config import ScanConfig
    >>> from media_audit.scanner import MediaScanner
    >>>
    >>> config = ScanConfig(root_paths=[Path("/media")])
    >>> scanner = MediaScanner(config)
    >>> result = scanner.scan()
    >>> print(f"Found {result.total_items} items with {result.total_issues} issues")

"""

from __future__ import annotations

import concurrent.futures
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
)

from media_audit.cache import MediaCache
from media_audit.config import ScanConfig
from media_audit.logging import get_logger
from media_audit.models import MovieItem, ScanResult, SeriesItem
from media_audit.parsers import MovieParser, TVParser
from media_audit.validator import MediaValidator


class MediaScanner:
    """Scans media libraries and validates content.

    Main scanner class that coordinates the discovery, parsing, and validation
    of media items. Supports concurrent processing and real-time progress updates.

    Attributes:
        config: Scan configuration settings
        console: Rich console for output
        logger: Logger instance for debugging
        cache: Media cache for performance
        movie_parser: Parser for movie content
        tv_parser: Parser for TV series content
        validator: Media validator instance

    """

    def __init__(self, config: ScanConfig):
        """Initialize scanner with configuration.

        Sets up parsers, validators, and cache based on the provided configuration.

        Args:
            config: Scan configuration with paths, patterns, and settings

        Raises:
            ValueError: If media patterns are not configured

        """
        self.config = config
        self.console = Console()
        self.logger = get_logger("scanner")
        self._cancelled = False
        self._cancel_lock = threading.Lock()

        # Initialize cache
        self.cache = MediaCache(cache_dir=config.cache_dir, enabled=config.cache_enabled)

        # Initialize parsers with compiled patterns
        if config.patterns is None:
            raise ValueError("Media patterns must be configured")
        patterns = config.patterns.compile_patterns()
        self.movie_parser = MovieParser(patterns, cache=self.cache)
        self.tv_parser = TVParser(patterns, cache=self.cache)

        # Initialize validator with cache
        self.validator = MediaValidator(config, cache=self.cache)

    def _check_for_esc(self) -> None:
        """Monitor for ESC key press to allow scan cancellation.

        Runs in a separate thread to detect ESC key presses. Supports both
        Windows (using msvcrt) and Unix-like systems (using termios).
        Sets the _cancelled flag when ESC is pressed.
        """
        if sys.platform == "win32":
            import msvcrt

            while not self._cancelled:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b"\x1b":  # ESC key
                        with self._cancel_lock:
                            self._cancelled = True
                            self.console.print(
                                "\n[yellow]Scan cancelled by user (ESC pressed)[/yellow]"
                            )
                        break
                time.sleep(0.1)
        else:
            # On Unix-like systems, use termios
            try:
                import select
                import termios
                import tty

                old_settings = termios.tcgetattr(sys.stdin)
                try:
                    tty.setcbreak(sys.stdin.fileno())
                    while not self._cancelled:
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            key = sys.stdin.read(1)
                            if key == "\x1b":  # ESC key
                                with self._cancel_lock:
                                    self._cancelled = True
                                    self.console.print(
                                        "\n[yellow]Scan cancelled by user (ESC pressed)[/yellow]"
                                    )
                                break
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except ImportError:
                # If termios not available, skip keyboard monitoring
                pass

    def is_cancelled(self) -> bool:
        """Check if scan has been cancelled.

        Thread-safe check of cancellation status.

        Returns:
            bool: True if scan was cancelled by user

        """
        with self._cancel_lock:
            return self._cancelled

    def scan(self) -> ScanResult:
        """Scan all configured root paths for media content.

        Main entry point for scanning. Discovers media files, parses metadata,
        validates content, and aggregates results. Supports cancellation via ESC key.

        Returns:
            ScanResult: Complete scan results including found media and issues

        Example:
            >>> scanner = MediaScanner(config)
            >>> result = scanner.scan()
            >>> for movie in result.movies:
            ...     if movie.has_issues:
            ...         print(f"{movie.name}: {len(movie.issues)} issues")

        """
        start_time = time.time()
        scan_time = datetime.now()
        self._cancelled = False

        result = ScanResult(
            scan_time=scan_time,
            duration=0,
            root_paths=self.config.root_paths,
        )

        # Start keyboard listener thread
        keyboard_thread = threading.Thread(target=self._check_for_esc, daemon=True)
        keyboard_thread.start()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                "Discovering media files... [dim](Press ESC to cancel)[/dim]", total=None
            )

            for root_path in self.config.root_paths:
                if self.is_cancelled():
                    result.errors.append("Scan cancelled by user")
                    break

                if not root_path.exists():
                    error_msg = f"Root path does not exist: {root_path}"
                    self.logger.error(error_msg)
                    result.errors.append(error_msg)
                    continue

                progress.update(
                    task,
                    description=f"Discovering media in {root_path}... [dim](Press ESC to cancel)[/dim]",
                )
                self._scan_path(root_path, result, progress)

        # Update duration
        result.duration = time.time() - start_time
        result.update_stats()

        # Show cache statistics
        if self.cache.enabled:
            stats = self.cache.get_stats()
            if stats["total"] > 0:
                self.console.print(
                    f"\n[dim]Cache: {stats['hits']} hits, {stats['misses']} misses "
                    f"({stats['hit_rate']:.1f}% hit rate)[/dim]"
                )

        return result

    def _scan_path(self, path: Path, result: ScanResult, progress: Progress | None = None) -> None:
        """Scan a single root path for media content.

        Looks for standard media directories (Movies, TV Shows) and processes
        their contents. Falls back to mixed content scanning if standard
        directories are not found.

        Args:
            path: Root path to scan
            result: ScanResult object to populate
            progress: Optional progress tracker for UI updates

        """
        # Look for Movies and TV directories
        movies_dir = path / "Movies"
        tv_dir = path / "TV Shows"

        # Also check alternative names
        if not tv_dir.exists():
            tv_dir = path / "TV"
        if not tv_dir.exists():
            tv_dir = path / "Series"

        # Scan movies
        if movies_dir.exists():
            self._scan_movies(movies_dir, result, progress, force_type="movie")

        # Scan TV shows
        if tv_dir.exists():
            self._scan_tv_shows(tv_dir, result, progress, force_type="tv")

        # Also scan root directory if no standard folders found
        if not movies_dir.exists() and not tv_dir.exists():
            self._scan_mixed_content(path, result, progress)

    def _scan_movies(
        self,
        movies_dir: Path,
        result: ScanResult,
        progress: Progress | None = None,
        force_type: str | None = None,
    ) -> None:
        """Scan a directory containing movies.

        Processes each subdirectory as a potential movie, using concurrent
        workers if configured. Updates progress in real-time.

        Args:
            movies_dir: Directory containing movie folders
            result: ScanResult to populate with found movies
            progress: Optional progress tracker
            force_type: Force content type (unused, for consistency)

        """
        movie_dirs = [d for d in movies_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        total_movies = len(movie_dirs)

        # Create a progress task for movies
        if progress:
            movie_task = progress.add_task(
                f"[cyan]Scanning {total_movies} movies... [dim](ESC to cancel)[/dim][/cyan]",
                total=total_movies,
            )

        if self.config.concurrent_workers > 1:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.concurrent_workers
            ) as executor:
                futures = {}
                for movie_dir in movie_dirs:
                    if self.is_cancelled():
                        break
                    # Force type to movie since we're in Movies folder
                    future = executor.submit(self._process_movie, movie_dir)
                    futures[future] = movie_dir

                for processed, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    if self.is_cancelled():
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    movie_dir = futures[future]
                    try:
                        movie = future.result()
                        if movie:
                            result.movies.append(movie)
                            if progress:
                                progress.update(
                                    movie_task,
                                    advance=1,
                                    description=f"[cyan]Movies: {processed}/{total_movies} - {movie.name}[/cyan]",
                                )
                    except Exception as e:
                        self.logger.exception(f"Error processing movie {movie_dir}: {e}")
                        result.errors.append(f"Error processing {movie_dir.name}: {str(e)}")
                        if progress:
                            progress.update(movie_task, advance=1)
        else:
            for i, movie_dir in enumerate(movie_dirs, 1):
                if self.is_cancelled():
                    break
                try:
                    # Force type to movie since we're in Movies folder
                    movie = self._process_movie(movie_dir)
                    if movie:
                        result.movies.append(movie)
                        if progress:
                            progress.update(
                                movie_task,
                                advance=1,
                                description=f"[cyan]Movies: {i}/{total_movies} - {movie.name}[/cyan]",
                            )
                except Exception as e:
                    self.logger.exception(f"Error processing movie {movie_dir}: {e}")
                    result.errors.append(f"Error processing {movie_dir.name}: {str(e)}")
                    if progress:
                        progress.update(movie_task, advance=1)

    def _scan_tv_shows(
        self,
        tv_dir: Path,
        result: ScanResult,
        progress: Progress | None = None,
        force_type: str | None = None,
    ) -> None:
        """Scan a directory containing TV series.

        Processes each subdirectory as a potential TV series, with support
        for concurrent processing. Each series is parsed with its complete
        season and episode hierarchy.

        Args:
            tv_dir: Directory containing TV series folders
            result: ScanResult to populate with found series
            progress: Optional progress tracker
            force_type: Force content type (unused, for consistency)

        """
        series_dirs = [d for d in tv_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        total_series = len(series_dirs)

        # Create a progress task for TV shows
        if progress:
            tv_task = progress.add_task(
                f"[magenta]Scanning {total_series} TV series... [dim](ESC to cancel)[/dim][/magenta]",
                total=total_series,
            )

        if self.config.concurrent_workers > 1:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.concurrent_workers
            ) as executor:
                futures = {}
                for series_dir in series_dirs:
                    if self.is_cancelled():
                        break
                    # Force type to TV since we're in TV Shows folder
                    future = executor.submit(self._process_series, series_dir)
                    futures[future] = series_dir

                for processed, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    if self.is_cancelled():
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    series_dir = futures[future]
                    try:
                        series = future.result()
                        if series:
                            result.series.append(series)
                            if progress:
                                progress.update(
                                    tv_task,
                                    advance=1,
                                    description=f"[magenta]TV Series: {processed}/{total_series} - {series.name}[/magenta]",
                                )
                    except Exception as e:
                        self.logger.exception(f"Error processing series {series_dir}: {e}")
                        result.errors.append(f"Error processing {series_dir.name}: {str(e)}")
                        if progress:
                            progress.update(tv_task, advance=1)
        else:
            for i, series_dir in enumerate(series_dirs, 1):
                if self.is_cancelled():
                    break
                try:
                    # Force type to TV since we're in TV Shows folder
                    series = self._process_series(series_dir)
                    if series:
                        result.series.append(series)
                        if progress:
                            progress.update(
                                tv_task,
                                advance=1,
                                description=f"[magenta]TV Series: {i}/{total_series} - {series.name}[/magenta]",
                            )
                except Exception as e:
                    self.logger.exception(f"Error processing series {series_dir}: {e}")
                    result.errors.append(f"Error processing {series_dir.name}: {str(e)}")
                    if progress:
                        progress.update(tv_task, advance=1)

    def _scan_mixed_content(
        self, path: Path, result: ScanResult, progress: Progress | None = None
    ) -> None:
        """Scan a directory that might contain both movies and TV shows.

        Analyzes each subdirectory to determine if it's a movie or TV series
        based on content structure. TV series are detected by presence of
        season folders.

        Args:
            path: Directory to scan for mixed content
            result: ScanResult to populate
            progress: Optional progress tracker

        """
        items = [item for item in path.iterdir() if item.is_dir() and not item.name.startswith(".")]
        total_items = len(items)

        if progress:
            mixed_task = progress.add_task(
                f"[yellow]Scanning {total_items} items... [dim](ESC to cancel)[/dim][/yellow]",
                total=total_items,
            )

        for i, item in enumerate(items, 1):
            if self.is_cancelled():
                break
            # Try to determine content type - check TV first since it's more specific (has season folders)
            if self.tv_parser.is_tv_directory(item):
                try:
                    series = self._process_series(item)
                    if series:
                        result.series.append(series)
                        if progress:
                            progress.update(
                                mixed_task,
                                advance=1,
                                description=f"[yellow]Items: {i}/{total_items} - Series: {series.name}[/yellow]",
                            )
                except Exception as e:
                    self.logger.exception(f"Error processing series {item}: {e}")
                    result.errors.append(f"Error processing {item.name}: {str(e)}")
                    if progress:
                        progress.update(mixed_task, advance=1)
            elif self.movie_parser.is_movie_directory(item):
                try:
                    movie = self._process_movie(item)
                    if movie:
                        result.movies.append(movie)
                        if progress:
                            progress.update(
                                mixed_task,
                                advance=1,
                                description=f"[yellow]Items: {i}/{total_items} - Movie: {movie.name}[/yellow]",
                            )
                except Exception as e:
                    self.logger.exception(f"Error processing movie {item}: {e}")
                    result.errors.append(f"Error processing {item.name}: {str(e)}")
                    if progress:
                        progress.update(mixed_task, advance=1)
            else:
                if progress:
                    progress.update(mixed_task, advance=1)

    def _process_movie(self, directory: Path) -> MovieItem | None:
        """Process a single movie directory.

        Parses movie metadata and runs validation checks.

        Args:
            directory: Path to movie directory

        Returns:
            MovieItem: Parsed and validated movie, or None if parsing failed

        """
        try:
            movie = self.movie_parser.parse(directory)
            if movie:
                self.validator.validate_movie(movie)
                self.logger.debug(f"Processed movie: {movie.name}")
            return movie
        except Exception as e:
            self.logger.error(f"Failed to process movie {directory}: {e}")
            return None

    def _process_series(self, directory: Path) -> SeriesItem | None:
        """Process a single TV series directory.

        Parses series structure including all seasons and episodes,
        then runs validation checks.

        Args:
            directory: Path to series directory

        Returns:
            SeriesItem: Parsed and validated series, or None if parsing failed

        """
        try:
            series = self.tv_parser.parse(directory)
            if series:
                self.validator.validate_series(series)
                self.logger.debug(f"Processed series: {series.name}")
            return series
        except Exception as e:
            self.logger.error(f"Failed to process series {directory}: {e}")
            return None
