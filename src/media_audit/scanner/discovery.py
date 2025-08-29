"""Path discovery module for finding media files."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

from media_audit.shared.logging import get_logger

if TYPE_CHECKING:
    from .config import ScannerConfig


class PathDiscovery:
    """Discovers media paths based on configuration."""

    MEDIA_EXTENSIONS = {
        ".mkv",
        ".mp4",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
        ".mpg",
        ".mpeg",
        ".3gp",
        ".ogv",
        ".ts",
        ".m2ts",
    }

    IGNORE_DIRS = {
        ".git",
        ".svn",
        "__pycache__",
        "node_modules",
        ".cache",
        "@eaDir",
        "#recycle",
        "$RECYCLE.BIN",
        "System Volume Information",
    }

    def __init__(self, config: ScannerConfig):
        """Initialize path discovery with config."""
        self.config = config
        self.logger = get_logger("discovery")

    def discover(self, root_path: Path) -> list[Path]:
        """Discover all media paths under root."""
        self.logger.debug(f"Discovering media in {root_path}")

        # Check if this path is named "Movies" or "TV Shows" - these are library containers
        base_name = root_path.name.lower()
        if base_name in ["movies", "tv shows", "tv", "series"]:
            # This is a library container, discover its contents
            return self._discover_generic(root_path)

        # Check if this is already a media item directory
        if self._is_content_directory(root_path, None):
            return [root_path]

        # Determine discovery strategy
        if self._is_library_root(root_path):
            return self._discover_library(root_path)
        else:
            return self._discover_generic(root_path)

    def _is_library_root(self, path: Path) -> bool:
        """Check if path is a library root with Movies/TV structure."""
        movies = path / "Movies"
        tv_shows = path / "TV Shows"
        tv_alt = path / "TV"

        return movies.exists() or tv_shows.exists() or tv_alt.exists()

    def _discover_library(self, root: Path) -> list[Path]:
        """Discover media in structured library."""
        paths = []

        # Check for Movies directory
        movies_dir = root / "Movies"
        if movies_dir.exists():
            paths.extend(self._find_content_dirs(movies_dir, "movie"))

        # Check for TV directories
        for tv_name in ["TV Shows", "TV", "Series"]:
            tv_dir = root / tv_name
            if tv_dir.exists():
                paths.extend(self._find_content_dirs(tv_dir, "tv"))
                break

        return paths

    def _discover_generic(self, root: Path) -> list[Path]:
        """Discover media in unstructured directory."""
        return self._find_content_dirs(root, None)

    def _find_content_dirs(self, base_path: Path, content_type: str | None) -> list[Path]:
        """Find content directories (movie folders or TV series folders)."""
        content_dirs = []

        try:
            for item in base_path.iterdir():
                # Skip hidden and system directories
                if item.name.startswith(".") or item.name in self.IGNORE_DIRS:
                    continue

                if not item.is_dir():
                    continue

                # Check exclusion patterns
                if self._is_excluded(item):
                    self.logger.debug(f"Excluded by pattern: {item}")
                    continue

                # Determine if this is a content directory
                if self._is_content_directory(item, content_type):
                    content_dirs.append(item)

        except PermissionError as e:
            self.logger.warning(f"Permission denied accessing {base_path}: {e}")

        return content_dirs

    def _is_content_directory(self, path: Path, hint: str | None) -> bool:
        """Check if directory contains media content."""
        # Look for video files
        has_videos = False
        has_season_dirs = False

        try:
            for item in path.iterdir():
                if item.is_file() and item.suffix.lower() in self.MEDIA_EXTENSIONS:
                    has_videos = True

                if item.is_dir() and self._is_season_dir(item.name):
                    has_season_dirs = True

                # Early exit if we found what we need
                if has_videos or has_season_dirs:
                    break

        except PermissionError:
            return False

        # TV series have season directories
        if has_season_dirs:
            return True

        # Movies have video files directly
        if has_videos and hint != "tv":
            return True

        # Check subdirectories for movies (e.g., Movie/Movie.mkv structure)
        if hint == "movie" or hint is None:
            for subdir in path.iterdir():
                if (
                    subdir.is_dir()
                    and not subdir.name.startswith(".")
                    and self._has_video_files(subdir)
                ):
                    return True

        return False

    def _is_season_dir(self, name: str) -> bool:
        """Check if directory name looks like a season."""
        name_lower = name.lower()
        return (
            name_lower.startswith("season")
            or name_lower.startswith("s0")
            or name_lower.startswith("s1")
            or name_lower.startswith("s2")
            or (name_lower == "specials")
        )

    def _has_video_files(self, path: Path) -> bool:
        """Check if directory contains video files."""
        try:
            for item in path.iterdir():
                if item.is_file() and item.suffix.lower() in self.MEDIA_EXTENSIONS:
                    return True
        except PermissionError:
            pass
        return False

    def _is_excluded(self, path: Path) -> bool:
        """Check if path matches exclusion patterns."""
        if not self.config.exclude_patterns:
            return False

        path_str = str(path)
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                return True

        return False
