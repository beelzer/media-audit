"""Base parser functionality."""

from __future__ import annotations

import re
from pathlib import Path

from media_audit.core import MediaAssets
from media_audit.domain.patterns import CompiledPatterns
from media_audit.infrastructure.cache import MediaCache
from media_audit.shared.logging import get_logger


class BaseParser:
    """Base class for media parsers."""

    VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".wmv", ".m4v", ".webm"}
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"}

    def __init__(self, patterns: CompiledPatterns, cache: MediaCache | None = None):
        """Initialize parser with compiled patterns."""
        self.patterns = patterns
        self.cache = cache
        self.logger = get_logger("parser")

    def is_video_file(self, path: Path) -> bool:
        """Check if file is a video."""
        return path.suffix.lower() in self.VIDEO_EXTENSIONS

    def is_image_file(self, path: Path) -> bool:
        """Check if file is an image."""
        return path.suffix.lower() in self.IMAGE_EXTENSIONS

    def match_pattern(self, filename: str, patterns: list[re.Pattern[str]]) -> bool:
        """Check if filename matches any pattern."""
        return any(pattern.search(filename) for pattern in patterns)

    def classify_asset(self, file_path: Path, base_path: Path) -> tuple[str, Path] | None:
        """Classify an asset file based on patterns."""
        is_image = self.is_image_file(file_path)
        is_video = file_path.suffix.lower() in {".mp4", ".mkv", ".mov", ".avi"}

        if not is_image and not is_video:
            return None

        # Get relative path for pattern matching
        try:
            rel_path = file_path.relative_to(base_path)
            filename = rel_path.as_posix()
        except ValueError as e:
            self.logger.debug(f"Failed to get relative path for {file_path}: {e}")
            filename = file_path.name

        # Check patterns - only image files can be posters, backgrounds, banners, title cards
        if is_image:
            if self.match_pattern(filename, self.patterns.poster_re):
                return ("poster", file_path)
            elif self.match_pattern(filename, self.patterns.background_re):
                return ("background", file_path)
            elif self.match_pattern(filename, self.patterns.banner_re):
                return ("banner", file_path)
            elif self.match_pattern(filename, self.patterns.title_card_re):
                return ("title_card", file_path)

        # Only video files can be trailers
        if is_video and self.match_pattern(filename, self.patterns.trailer_re):
            return ("trailer", file_path)

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
                    match asset_type:
                        case "poster":
                            assets.posters.append(path)
                        case "background":
                            assets.backgrounds.append(path)
                        case "banner":
                            assets.banners.append(path)
                        case "trailer":
                            assets.trailers.append(path)
                        case "title_card":
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

    def extract_imdb_id(self, text: str) -> str | None:
        """Extract IMDB ID from text."""
        match = re.search(r"(?:imdb[-_]?)?(tt\d{7,8})", text, re.IGNORECASE)
        return match.group(1) if match else None

    def extract_release_group(self, text: str) -> str | None:
        """Extract release group from filename."""
        # Common pattern: -GROUP at end or [GROUP] at end
        patterns = [
            r"-([A-Za-z0-9]+)(?:\.\w{3,4})?$",  # -GROUP.ext
            r"\[([A-Za-z0-9]+)\](?:\.\w{3,4})?$",  # [GROUP].ext
            r"-([A-Za-z0-9]+)\s*(?:\[|$)",  # -GROUP followed by [ or end
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    def extract_quality(self, text: str) -> str | None:
        """Extract quality from filename."""
        qualities = ["2160p", "4K", "1080p", "720p", "480p", "360p", "UHD", "FHD", "HD", "SD"]
        text_upper = text.upper()
        for quality in qualities:
            if quality.upper() in text_upper:
                return quality
        return None

    def extract_source(self, text: str) -> str | None:
        """Extract source from filename."""
        # Order matters - check more specific patterns first
        sources = [
            ("WEB-DL", "WEBDL"),
            ("WEBRip", "WEBRIP"),
            ("BluRay", "BLURAY"),
            ("Blu-Ray", "BLURAY"),
            ("BDRip", "BDRIP"),
            ("BRRip", "BRRIP"),
            ("HDTVRip", "HDTVRIP"),
            ("HDTV", "HDTV"),
            ("DVDRip", "DVDRIP"),
            ("DVDSCR", "DVDSCR"),
            ("DVD", "DVD"),
            ("CAM", "CAM"),
            ("TS", "TS"),
            ("TC", "TC"),
            ("SCR", "SCR"),
            ("WEB", "WEB"),
            ("BD", "BD"),
        ]

        # Normalize text but keep some separation
        text_normalized = text.upper()
        # Replace common separators with spaces for better word detection
        for sep in ["-", ".", "_", "[", "]", "(", ")"]:
            text_normalized = text_normalized.replace(sep, " ")

        for source_orig, source_pattern in sources:
            # Check if the source pattern exists in the normalized text
            if source_pattern in text_normalized.replace(" ", ""):
                return source_orig.replace("-", "")

        return None
