"""Base parser functionality."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..models import MediaAssets, MediaItem
from ..patterns import CompiledPatterns


class BaseParser:
    """Base class for media parsers."""

    VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".wmv", ".m4v", ".webm"}
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"}

    def __init__(self, patterns: CompiledPatterns):
        """Initialize parser with compiled patterns."""
        self.patterns = patterns

    def is_video_file(self, path: Path) -> bool:
        """Check if file is a video."""
        return path.suffix.lower() in self.VIDEO_EXTENSIONS

    def is_image_file(self, path: Path) -> bool:
        """Check if file is an image."""
        return path.suffix.lower() in self.IMAGE_EXTENSIONS

    def match_pattern(self, filename: str, patterns: list[re.Pattern[str]]) -> bool:
        """Check if filename matches any pattern."""
        for pattern in patterns:
            if pattern.search(filename):
                return True
        return False

    def classify_asset(self, file_path: Path, base_path: Path) -> tuple[str, Path] | None:
        """Classify an asset file based on patterns."""
        if not self.is_image_file(file_path) and not file_path.is_dir():
            if not file_path.suffix.lower() in {".mp4", ".mkv", ".mov", ".avi"}:
                return None

        # Get relative path for pattern matching
        try:
            rel_path = file_path.relative_to(base_path)
            filename = rel_path.as_posix()
        except ValueError:
            filename = file_path.name

        # Check patterns
        if self.match_pattern(filename, self.patterns.poster_re):
            return ("poster", file_path)
        elif self.match_pattern(filename, self.patterns.background_re):
            return ("background", file_path)
        elif self.match_pattern(filename, self.patterns.banner_re):
            return ("banner", file_path)
        elif self.match_pattern(filename, self.patterns.trailer_re):
            return ("trailer", file_path)
        elif self.match_pattern(filename, self.patterns.title_card_re):
            return ("title_card", file_path)

        return None

    def scan_assets(self, directory: Path) -> MediaAssets:
        """Scan directory for media assets."""
        assets = MediaAssets()

        # Scan main directory and subdirectories
        for item in directory.rglob("*"):
            if item.is_file():
                classification = self.classify_asset(item, directory)
                if classification:
                    asset_type, path = classification
                    if asset_type == "poster":
                        assets.posters.append(path)
                    elif asset_type == "background":
                        assets.backgrounds.append(path)
                    elif asset_type == "banner":
                        assets.banners.append(path)
                    elif asset_type == "trailer":
                        assets.trailers.append(path)
                    elif asset_type == "title_card":
                        assets.title_cards.append(path)

        return assets

    def parse_year(self, text: str) -> int | None:
        """Extract year from text."""
        match = re.search(r"\((\d{4})\)", text)
        if match:
            year = int(match.group(1))
            if 1900 <= year <= 2100:  # Reasonable year range
                return year
        return None