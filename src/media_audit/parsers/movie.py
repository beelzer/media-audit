"""Movie parser implementation."""

from __future__ import annotations

import re
from pathlib import Path

from media_audit.models import MediaType, MovieItem, VideoInfo

from .base import BaseParser


class MovieParser(BaseParser):
    """Parser for movie content."""

    def parse(self, directory: Path) -> MovieItem | None:
        """Parse a movie directory."""
        if not directory.is_dir():
            return None

        # Extract movie name and year
        folder_name = directory.name
        year = self.parse_year(folder_name)

        # Extract additional metadata from folder name
        imdb_id = self.extract_imdb_id(folder_name)

        # Clean movie name - remove year and IMDB ID
        movie_name = folder_name
        movie_name = re.sub(r"\s*\(\d{4}\)\s*", "", movie_name)  # Remove year
        movie_name = re.sub(r"\s*\{[^}]*\}\s*", "", movie_name)  # Remove {imdb-...}
        movie_name = movie_name.strip()

        # Create movie item
        movie = MovieItem(
            path=directory,
            name=movie_name,
            type=MediaType.MOVIE,
            year=year,
            imdb_id=imdb_id,
        )

        # Scan for assets
        movie.assets = self.scan_assets(directory)

        # Find main video file
        video_files = []
        for file_path in directory.iterdir():
            if file_path.is_file() and self.is_video_file(file_path):
                # Exclude sample files and trailers
                name_lower = file_path.name.lower()
                if not any(x in name_lower for x in ["sample", "trailer", "preview"]):
                    video_files.append(file_path)

        # Use largest video file as main movie
        if video_files:
            main_video = max(video_files, key=lambda p: p.stat().st_size)
            movie.video_info = VideoInfo(path=main_video)

            # Extract metadata from video filename
            video_name = main_video.stem
            if not movie.imdb_id:
                movie.imdb_id = self.extract_imdb_id(video_name)
            if not movie.quality:
                movie.quality = self.extract_quality(video_name)
            if not movie.source:
                movie.source = self.extract_source(video_name)
            if not movie.release_group:
                movie.release_group = self.extract_release_group(video_name)

        return movie

    def is_movie_directory(self, directory: Path) -> bool:
        """Check if directory appears to be a movie."""
        if not directory.is_dir():
            return False

        # Check for season folders - if present, it's a TV show
        has_season_folders = any(
            d.is_dir() and re.match(r"^Season\s*\d+|^S\d+", d.name, re.IGNORECASE)
            for d in directory.iterdir()
        )

        if has_season_folders:
            return False

        # Check for video files - must have at least one to be a movie
        has_video = any(f.is_file() and self.is_video_file(f) for f in directory.iterdir())
        return has_video
