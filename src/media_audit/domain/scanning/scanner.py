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
    >>> from media_audit.infrastructure.config import ScanConfig
    >>> from media_audit.domain.scanning import MediaScanner
    >>>
    >>> config = ScanConfig(root_paths=[Path("/media")])
    >>> scanner = MediaScanner(config)
    >>> result = scanner.scan()
    >>> print(f"Found {result.total_items} items with {result.total_issues} issues")

"""

from __future__ import annotations

import asyncio
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
)

from media_audit.core import MovieItem, ScanResult, SeriesItem
from media_audit.domain.parsing import MovieParser, TVParser
from media_audit.domain.validation import MediaValidator
from media_audit.infrastructure.cache import MediaCache
from media_audit.shared.logging import get_logger

if TYPE_CHECKING:
    from media_audit.infrastructure.config import ScanConfig


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
                # Check if stdin is available and is a tty
                if not hasattr(sys.stdin, "fileno") or not sys.stdin.isatty():
                    return  # Skip in non-interactive environments (CI, redirected input)

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
            except (ImportError, OSError, AttributeError):
                # Windows, non-interactive environment, or CI
                pass

    def is_cancelled(self) -> bool:
        """Check if scan has been cancelled.

        Thread-safe check of cancellation status.

        Returns:
            bool: True if scan was cancelled by user

        """
        with self._cancel_lock:
            return self._cancelled

    async def scan(self) -> ScanResult:
        """Scan media libraries based on configuration.

        Main async entry point for the scanning process. Discovers and processes
        all media in configured root paths.

        Returns:
            ScanResult: Comprehensive scan results with all discovered media

        """
        result = ScanResult(
            scan_time=datetime.now(),
            duration=0,
            root_paths=self.config.root_paths,
            errors=[],
        )

        # Start ESC key monitoring in background thread
        esc_thread = threading.Thread(target=self._check_for_esc, daemon=True)
        esc_thread.start()

        start_time = time.time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task("[bold cyan]Starting media scan...", total=None)

            # Process each root path
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
                await self._scan_path(root_path, result, progress)

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

    async def _scan_path(
        self, path: Path, result: ScanResult, progress: Progress | None = None
    ) -> None:
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

        # Scan movies and TV shows concurrently
        tasks = []
        if movies_dir.exists():
            tasks.append(self._scan_movies(movies_dir, result, progress, force_type="movie"))
        if tv_dir.exists():
            tasks.append(self._scan_tv_shows(tv_dir, result, progress, force_type="tv"))

        # Also scan root directory if no standard folders found
        if not movies_dir.exists() and not tv_dir.exists():
            tasks.append(self._scan_mixed_content(path, result, progress))

        if tasks:
            await asyncio.gather(*tasks)

    async def _scan_movies(
        self,
        movies_dir: Path,
        result: ScanResult,
        progress: Progress | None = None,
        force_type: str | None = None,
    ) -> None:
        """Scan a directory containing movies.

        Processes each subdirectory as a potential movie, using concurrent
        async tasks. Updates progress in real-time.

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

        # Process movies concurrently with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.config.concurrent_workers)

        async def process_with_semaphore(movie_dir: Path) -> MovieItem | None:
            async with semaphore:
                return await self._process_movie(movie_dir)

        tasks = []
        for movie_dir in movie_dirs:
            if self.is_cancelled():
                break
            task = asyncio.create_task(process_with_semaphore(movie_dir))
            tasks.append(task)

        try:
            # Process all movies concurrently
            for i, coro in enumerate(asyncio.as_completed(tasks), 1):
                if self.is_cancelled():
                    # Cancel all remaining tasks
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    # Wait for tasks to complete cancellation
                    await asyncio.gather(*tasks, return_exceptions=True)
                    break
                try:
                    movie = await coro
                    if movie:
                        result.movies.append(movie)
                        if progress:
                            progress.update(
                                movie_task,
                                advance=1,
                                description=f"[cyan]Movies: {i}/{total_movies} - {movie.name}[/cyan]",
                            )
                except asyncio.CancelledError:
                    # Task was cancelled, just continue
                    if progress:
                        progress.update(movie_task, advance=1)
                except Exception as e:
                    self.logger.error(f"Error processing movie: {e}", exc_info=True)
                    result.errors.append(f"Error processing movie: {str(e)}")
                    if progress:
                        progress.update(movie_task, advance=1)
        finally:
            # Ensure all tasks are cleaned up
            for task in tasks:
                if not task.done():
                    task.cancel()
            # Wait for all tasks to finish
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _scan_tv_shows(
        self,
        tv_dir: Path,
        result: ScanResult,
        progress: Progress | None = None,
        force_type: str | None = None,
    ) -> None:
        """Scan a directory containing TV series.

        Processes each subdirectory as a potential TV series, with support
        for concurrent async processing. Each series is parsed with its complete
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

        # Process series concurrently with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.config.concurrent_workers)

        async def process_with_semaphore(series_dir: Path) -> SeriesItem | None:
            async with semaphore:
                return await self._process_series(series_dir)

        tasks = []
        for series_dir in series_dirs:
            if self.is_cancelled():
                break
            task = asyncio.create_task(process_with_semaphore(series_dir))
            tasks.append(task)

        try:
            # Process all series concurrently
            for i, coro in enumerate(asyncio.as_completed(tasks), 1):
                if self.is_cancelled():
                    # Cancel all remaining tasks
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    # Wait for tasks to complete cancellation
                    await asyncio.gather(*tasks, return_exceptions=True)
                    break
                try:
                    series = await coro
                    if series:
                        result.series.append(series)
                        if progress:
                            progress.update(
                                tv_task,
                                advance=1,
                                description=f"[magenta]TV Series: {i}/{total_series} - {series.name}[/magenta]",
                            )
                except asyncio.CancelledError:
                    # Task was cancelled, just continue
                    if progress:
                        progress.update(tv_task, advance=1)
                except Exception as e:
                    self.logger.error(f"Error processing series: {e}", exc_info=True)
                    result.errors.append(f"Error processing series: {str(e)}")
                    if progress:
                        progress.update(tv_task, advance=1)
        finally:
            # Ensure all tasks are cleaned up
            for task in tasks:
                if not task.done():
                    task.cancel()
            # Wait for all tasks to finish
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _scan_mixed_content(
        self, path: Path, result: ScanResult, progress: Progress | None = None
    ) -> None:
        """Scan a directory that might contain both movies and TV shows.

        Analyzes each subdirectory to determine if it's a movie or TV series
        based on content structure. TV series are detected by presence of
        season folders.

        Args:
            path: Directory to scan for mixed content
            result: ScanResult to populate with discovered items
            progress: Optional progress tracker

        """
        items = [d for d in path.iterdir() if d.is_dir() and not d.name.startswith(".")]
        total_items = len(items)

        if progress:
            mixed_task = progress.add_task(
                f"[yellow]Scanning {total_items} items... [dim](ESC to cancel)[/dim][/yellow]",
                total=total_items,
            )

        # Process items concurrently with semaphore
        semaphore = asyncio.Semaphore(self.config.concurrent_workers)

        async def process_item(item: Path) -> tuple[str, Any | None]:
            async with semaphore:
                if self.tv_parser.is_tv_directory(item):
                    series = await self._process_series(item)
                    return ("series", series)
                elif self.movie_parser.is_movie_directory(item):
                    movie = await self._process_movie(item)
                    return ("movie", movie)
                return ("unknown", None)

        tasks = []
        for item in items:
            if self.is_cancelled():
                break
            task = asyncio.create_task(process_item(item))
            tasks.append(task)

        try:
            # Process all items concurrently
            for i, coro in enumerate(asyncio.as_completed(tasks), 1):
                if self.is_cancelled():
                    # Cancel all remaining tasks
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    # Wait for tasks to complete cancellation
                    await asyncio.gather(*tasks, return_exceptions=True)
                    break
                try:
                    item_type, media_item = await coro
                    if item_type == "series" and media_item:
                        result.series.append(media_item)
                        if progress:
                            progress.update(
                                mixed_task,
                                advance=1,
                                description=f"[yellow]Items: {i}/{total_items} - TV Series: {media_item.name}[/yellow]",
                            )
                    elif item_type == "movie" and media_item:
                        result.movies.append(media_item)
                        if progress:
                            progress.update(
                                mixed_task,
                                advance=1,
                                description=f"[yellow]Items: {i}/{total_items} - Movie: {media_item.name}[/yellow]",
                            )
                    else:
                        if progress:
                            progress.update(mixed_task, advance=1)
                except asyncio.CancelledError:
                    # Task was cancelled, just continue
                    if progress:
                        progress.update(mixed_task, advance=1)
                except Exception as e:
                    self.logger.exception(f"Error processing item: {e}")
                    result.errors.append(f"Error processing item: {str(e)}")
                    if progress:
                        progress.update(mixed_task, advance=1)
        finally:
            # Ensure all tasks are cleaned up
            for task in tasks:
                if not task.done():
                    task.cancel()
            # Wait for all tasks to finish
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_movie(self, directory: Path) -> MovieItem | None:
        """Process a single movie directory.

        Parses movie metadata and runs validation checks.

        Args:
            directory: Path to movie directory

        Returns:
            MovieItem: Parsed and validated movie, or None if parsing failed

        """
        try:
            movie = await self.movie_parser.parse(directory)
            if movie:
                await self.validator.validate_movie(movie)
                self.logger.debug(f"Processed movie: {movie.name}")
            return movie
        except Exception as e:
            self.logger.error(f"Failed to process movie {directory}: {e}")
            return None

    async def _process_series(self, directory: Path) -> SeriesItem | None:
        """Process a single TV series directory.

        Parses series structure including all seasons and episodes,
        then runs validation checks.

        Args:
            directory: Path to series directory

        Returns:
            SeriesItem: Parsed and validated series, or None if parsing failed

        """
        try:
            series = await self.tv_parser.parse(directory)
            if series:
                await self.validator.validate_series(series)
                self.logger.debug(f"Processed series: {series.name}")
            return series
        except Exception as e:
            self.logger.error(f"Failed to process series {directory}: {e}")
            return None
