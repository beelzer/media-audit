"""Movie parser implementation."""

from __future__ import annotations

import re
from pathlib import Path

from ..models import MovieItem, VideoInfo
from ..patterns import CompiledPatterns
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
        
        # Clean movie name
        movie_name = re.sub(r"\s*\(\d{4}\)\s*$", "", folder_name).strip()

        # Create movie item
        movie = MovieItem(
            path=directory,
            name=movie_name,
            year=year,
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

        return movie

    def is_movie_directory(self, directory: Path) -> bool:
        """Check if directory appears to be a movie."""
        if not directory.is_dir():
            return False

        # Check for year pattern in folder name
        if self.parse_year(directory.name):
            return True

        # Check for video files
        has_video = any(
            f.is_file() and self.is_video_file(f)
            for f in directory.iterdir()
        )

        # Movies typically don't have Season folders
        has_season_folders = any(
            d.is_dir() and re.match(r"^Season\s*\d+", d.name, re.IGNORECASE)
            for d in directory.iterdir()
        )

        return has_video and not has_season_folders