"""Main media scanner implementation."""

from __future__ import annotations

import concurrent.futures
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..models import ScanResult
from ..parsers import MovieParser, TVParser
from ..validator import MediaValidator

if TYPE_CHECKING:
    from ..config import ScanConfig


class MediaScanner:
    """Scans media libraries and validates content."""

    def __init__(self, config: ScanConfig):
        """Initialize scanner with configuration."""
        self.config = config
        self.console = Console()
        
        # Initialize parsers with compiled patterns
        patterns = config.patterns.compile_patterns()
        self.movie_parser = MovieParser(patterns)
        self.tv_parser = TVParser(patterns)
        
        # Initialize validator
        self.validator = MediaValidator(config)

    def scan(self) -> ScanResult:
        """Scan all configured root paths."""
        start_time = time.time()
        scan_time = datetime.now()

        result = ScanResult(
            scan_time=scan_time,
            duration=0,
            root_paths=self.config.root_paths,
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Scanning media libraries...", total=None)

            for root_path in self.config.root_paths:
                if not root_path.exists():
                    result.errors.append(f"Root path does not exist: {root_path}")
                    continue

                progress.update(task, description=f"Scanning {root_path}...")
                self._scan_path(root_path, result)

        # Update duration
        result.duration = time.time() - start_time
        result.update_stats()

        return result

    def _scan_path(self, path: Path, result: ScanResult) -> None:
        """Scan a single path for media content."""
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
            self._scan_movies(movies_dir, result)
        
        # Scan TV shows
        if tv_dir.exists():
            self._scan_tv_shows(tv_dir, result)

        # Also scan root directory if no standard folders found
        if not movies_dir.exists() and not tv_dir.exists():
            self._scan_mixed_content(path, result)

    def _scan_movies(self, movies_dir: Path, result: ScanResult) -> None:
        """Scan a movies directory."""
        movie_dirs = [
            d for d in movies_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

        if self.config.concurrent_workers > 1:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.concurrent_workers
            ) as executor:
                futures = []
                for movie_dir in movie_dirs:
                    future = executor.submit(self._process_movie, movie_dir)
                    futures.append(future)

                for future in concurrent.futures.as_completed(futures):
                    try:
                        movie = future.result()
                        if movie:
                            result.movies.append(movie)
                    except Exception as e:
                        result.errors.append(f"Error processing movie: {e}")
        else:
            for movie_dir in movie_dirs:
                try:
                    movie = self._process_movie(movie_dir)
                    if movie:
                        result.movies.append(movie)
                except Exception as e:
                    result.errors.append(f"Error processing {movie_dir}: {e}")

    def _scan_tv_shows(self, tv_dir: Path, result: ScanResult) -> None:
        """Scan a TV shows directory."""
        series_dirs = [
            d for d in tv_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

        if self.config.concurrent_workers > 1:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.concurrent_workers
            ) as executor:
                futures = []
                for series_dir in series_dirs:
                    future = executor.submit(self._process_series, series_dir)
                    futures.append(future)

                for future in concurrent.futures.as_completed(futures):
                    try:
                        series = future.result()
                        if series:
                            result.series.append(series)
                    except Exception as e:
                        result.errors.append(f"Error processing series: {e}")
        else:
            for series_dir in series_dirs:
                try:
                    series = self._process_series(series_dir)
                    if series:
                        result.series.append(series)
                except Exception as e:
                    result.errors.append(f"Error processing {series_dir}: {e}")

    def _scan_mixed_content(self, path: Path, result: ScanResult) -> None:
        """Scan a directory that might contain both movies and TV shows."""
        for item in path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                # Try to determine content type
                if self.movie_parser.is_movie_directory(item):
                    try:
                        movie = self._process_movie(item)
                        if movie:
                            result.movies.append(movie)
                    except Exception as e:
                        result.errors.append(f"Error processing {item}: {e}")
                elif self.tv_parser.is_tv_directory(item):
                    try:
                        series = self._process_series(item)
                        if series:
                            result.series.append(series)
                    except Exception as e:
                        result.errors.append(f"Error processing {item}: {e}")

    def _process_movie(self, directory: Path) -> MovieItem | None:
        """Process a single movie directory."""
        movie = self.movie_parser.parse(directory)
        if movie:
            self.validator.validate_movie(movie)
        return movie

    def _process_series(self, directory: Path) -> SeriesItem | None:
        """Process a single TV series directory."""
        series = self.tv_parser.parse(directory)
        if series:
            self.validator.validate_series(series)
        return series