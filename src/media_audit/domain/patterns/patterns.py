"""Pattern definitions for different media server types using Python 3.13 features."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from re import Pattern

from media_audit.shared.logging import get_logger

# Type aliases for better readability
type PatternList = list[str]
type CompiledPatternList = list[Pattern[str]]

logger = get_logger(__name__)


class ServerProfile(StrEnum):
    """Supported media server profiles."""

    PLEX = "plex"
    JELLYFIN = "jellyfin"
    EMBY = "emby"
    KODI = "kodi"
    ALL = "all"


@dataclass(slots=True)
class MediaPatterns:
    """Collection of patterns for matching media files using slots for efficiency."""

    poster_patterns: PatternList = field(default_factory=list)
    background_patterns: PatternList = field(default_factory=list)
    banner_patterns: PatternList = field(default_factory=list)
    trailer_patterns: PatternList = field(default_factory=list)
    title_card_patterns: PatternList = field(default_factory=list)
    subtitle_patterns: PatternList = field(default_factory=list)
    nfo_patterns: PatternList = field(default_factory=list)

    def compile_patterns(self) -> CompiledPatterns:
        """Compile regex patterns for efficient matching."""
        return CompiledPatterns(
            poster_re=self._compile_list(self.poster_patterns),
            background_re=self._compile_list(self.background_patterns),
            banner_re=self._compile_list(self.banner_patterns),
            trailer_re=self._compile_list(self.trailer_patterns),
            title_card_re=self._compile_list(self.title_card_patterns),
            subtitle_re=self._compile_list(self.subtitle_patterns),
            nfo_re=self._compile_list(self.nfo_patterns),
        )

    @staticmethod
    def _compile_list(patterns: PatternList) -> CompiledPatternList:
        """Compile a list of patterns using list comprehension."""
        return [re.compile(p, re.IGNORECASE) for p in patterns]

    def merge(self, other: MediaPatterns) -> MediaPatterns:
        """Merge with another pattern set using unpacking."""
        return MediaPatterns(
            poster_patterns=[*self.poster_patterns, *other.poster_patterns],
            background_patterns=[*self.background_patterns, *other.background_patterns],
            banner_patterns=[*self.banner_patterns, *other.banner_patterns],
            trailer_patterns=[*self.trailer_patterns, *other.trailer_patterns],
            title_card_patterns=[*self.title_card_patterns, *other.title_card_patterns],
            subtitle_patterns=[*self.subtitle_patterns, *other.subtitle_patterns],
            nfo_patterns=[*self.nfo_patterns, *other.nfo_patterns],
        )


@dataclass(slots=True)
class CompiledPatterns:
    """Compiled regex patterns for matching using slots."""

    poster_re: CompiledPatternList = field(default_factory=list)
    background_re: CompiledPatternList = field(default_factory=list)
    banner_re: CompiledPatternList = field(default_factory=list)
    trailer_re: CompiledPatternList = field(default_factory=list)
    title_card_re: CompiledPatternList = field(default_factory=list)
    subtitle_re: CompiledPatternList = field(default_factory=list)
    nfo_re: CompiledPatternList = field(default_factory=list)

    def match_file(self, filepath: Path) -> str | None:
        """Match a file against patterns using match/case."""
        filename = filepath.name

        # Using match/case for cleaner pattern matching
        match filepath.suffix.lower():
            case ".jpg" | ".jpeg" | ".png" | ".webp":
                if self._matches_any(filename, self.poster_re):
                    return "poster"
                elif self._matches_any(filename, self.background_re):
                    return "background"
                elif self._matches_any(filename, self.banner_re):
                    return "banner"
                elif self._matches_any(filename, self.title_card_re):
                    return "title_card"
            case ".mp4" | ".mkv" | ".avi" | ".mov":
                if self._matches_any(filename, self.trailer_re):
                    return "trailer"
            case ".srt" | ".sub" | ".ass" | ".ssa" | ".vtt":
                return "subtitle"
            case ".nfo":
                return "nfo"
            case _:
                return None

        return None

    @staticmethod
    def _matches_any(text: str, patterns: CompiledPatternList) -> bool:
        """Check if text matches any pattern using any() with generator."""
        return any(pattern.search(text) for pattern in patterns)


# Pattern definitions using modern dict merge
BASE_PATTERNS = MediaPatterns(
    poster_patterns=[
        r"^poster\.",
        r"^folder\.",
        r"^cover\.",
    ],
    background_patterns=[
        r"^fanart\.",
        r"^background\.",
        r"^backdrop\.",
    ],
    subtitle_patterns=[
        r"\.srt$",
        r"\.sub$",
        r"\.ass$",
        r"\.ssa$",
        r"\.vtt$",
    ],
    nfo_patterns=[
        r"\.nfo$",
    ],
)

# Plex-specific patterns
PLEX_PATTERNS = MediaPatterns(
    poster_patterns=[
        *BASE_PATTERNS.poster_patterns,
        r"^movie\.",
        r"^default\.",
        r"^poster-\d+\.",
    ],
    background_patterns=[
        *BASE_PATTERNS.background_patterns,
        r"^art\.",
        r"-fanart\.",
        r"^fanart-\d+\.",
    ],
    banner_patterns=[
        r"^banner\.",
        r"-banner\.",
        r"^banner-\d+\.",
    ],
    trailer_patterns=[
        r"-trailer\.",
        r"^trailer\.",
        r"^trailers/.*",
    ],
    title_card_patterns=[
        r"^S\d{2}E\d{2}\.",
        r"^S\d{2}E\d{2}-thumb\.",
    ],
    subtitle_patterns=BASE_PATTERNS.subtitle_patterns,
    nfo_patterns=BASE_PATTERNS.nfo_patterns,
)

# Jellyfin-specific patterns
JELLYFIN_PATTERNS = MediaPatterns(
    poster_patterns=[
        *BASE_PATTERNS.poster_patterns,
        r"^poster-\d+\.",
        r"^poster\d+\.",
    ],
    background_patterns=[
        *BASE_PATTERNS.background_patterns,
        r"^backdrop\d+\.",
        r"^backdrop-\d+\.",
    ],
    banner_patterns=[
        r"^banner\.",
        r"^banner-\d+\.",
    ],
    trailer_patterns=[
        r"-trailer\.",
        r"^trailers/.*",
    ],
    title_card_patterns=[
        r"^S\d{2}E\d{2}-thumb\.",
    ],
    subtitle_patterns=BASE_PATTERNS.subtitle_patterns,
    nfo_patterns=BASE_PATTERNS.nfo_patterns,
)

# Emby patterns (similar to Jellyfin with some extras)
EMBY_PATTERNS = MediaPatterns(
    poster_patterns=JELLYFIN_PATTERNS.poster_patterns,
    background_patterns=[
        *JELLYFIN_PATTERNS.background_patterns,
        r"^extrafanart/.*",  # Emby specific
    ],
    banner_patterns=JELLYFIN_PATTERNS.banner_patterns,
    trailer_patterns=JELLYFIN_PATTERNS.trailer_patterns,
    title_card_patterns=JELLYFIN_PATTERNS.title_card_patterns,
    subtitle_patterns=JELLYFIN_PATTERNS.subtitle_patterns,
    nfo_patterns=JELLYFIN_PATTERNS.nfo_patterns,
)

# Kodi patterns
KODI_PATTERNS = MediaPatterns(
    poster_patterns=[
        *BASE_PATTERNS.poster_patterns,
        r"^movie-poster\.",
        r"^season-all-poster\.",
        r"^season\d{2}-poster\.",
    ],
    background_patterns=[
        *BASE_PATTERNS.background_patterns,
        r"^movie-fanart\.",
        r"^season-all-fanart\.",
    ],
    banner_patterns=[
        r"^movie-banner\.",
        r"^season-all-banner\.",
    ],
    trailer_patterns=[
        r"-trailer\.",
        r"\.trailer\.",
    ],
    title_card_patterns=[
        r"^S\d{2}E\d{2}\.",
    ],
    subtitle_patterns=BASE_PATTERNS.subtitle_patterns,
    nfo_patterns=BASE_PATTERNS.nfo_patterns,
)

# Combined patterns for all profiles
ALL_PATTERNS = PLEX_PATTERNS.merge(JELLYFIN_PATTERNS).merge(KODI_PATTERNS)


# Profile mapping using match/case
def get_patterns(profiles: list[str] | None = None) -> MediaPatterns:
    """Get patterns for specified profiles using match/case."""
    if not profiles:
        profiles = [ServerProfile.ALL]

    combined = MediaPatterns()

    for profile in profiles:
        profile_lower = profile.lower()

        # Using match/case for profile selection
        match profile_lower:
            case ServerProfile.PLEX:
                combined = combined.merge(PLEX_PATTERNS)
            case ServerProfile.JELLYFIN:
                combined = combined.merge(JELLYFIN_PATTERNS)
            case ServerProfile.EMBY:
                combined = combined.merge(EMBY_PATTERNS)
            case ServerProfile.KODI:
                combined = combined.merge(KODI_PATTERNS)
            case ServerProfile.ALL | _:
                combined = ALL_PATTERNS

    return combined


# Movie name patterns using raw strings
MOVIE_PATTERNS: list[str] = [
    r"^(.+?)\s*\((\d{4})\)",  # Movie Name (Year)
    r"^(.+?)\s*\[(\d{4})\]",  # Movie Name [Year]
    r"^(.+?)\s+(\d{4})",  # Movie Name Year
]

# TV show patterns
TV_PATTERNS: list[str] = [
    r"^(.+?)\s*\((\d{4})\)",  # Show Name (Year)
    r"^(.+?)\s*-\s*(.+)",  # Show Name - Description
    r"^(.+?)$",  # Show Name
]

# Episode patterns using f-strings in comments for clarity
EPISODE_PATTERNS: list[str] = [
    r"[Ss](\d+)[Ee](\d+)",  # S01E01
    r"(\d+)x(\d+)",  # 1x01
    r"[Ss](\d+)\s*-\s*[Ee](\d+)",  # S01 - E01
    r"Season\s*(\d+).*Episode\s*(\d+)",  # Season 1 Episode 1
]

# Season patterns
SEASON_PATTERNS: list[str] = [
    r"Season\s*(\d+)",  # Season 1
    r"S(\d+)",  # S01
    r"Series\s*(\d+)",  # Series 1
    r"Specials?",  # Specials
]

# File exclusion patterns
DEFAULT_EXCLUSIONS: list[str] = [
    "@eaDir",  # Synology metadata
    ".DS_Store",  # macOS metadata
    "Thumbs.db",  # Windows thumbnails
    "#recycle",  # Synology recycle bin
    "$RECYCLE.BIN",  # Windows recycle bin
    ".AppleDouble",  # macOS metadata
    ".LSOverride",  # macOS metadata
    "desktop.ini",  # Windows metadata
    ".BridgeCache",  # Adobe Bridge cache
    ".BridgeCacheT",  # Adobe Bridge cache
    "System Volume Information",  # Windows system
    "lost+found",  # Linux system
    ".TemporaryItems",  # macOS temp
    ".Spotlight-V100",  # macOS Spotlight
    ".DocumentRevisions-V100",  # macOS versions
    ".fseventsd",  # macOS events
    ".Trash",  # macOS trash
    ".VolumeIcon.icns",  # macOS volume icon
    ".com.apple",  # macOS metadata
    ".apdisk",  # macOS metadata
]


def match_movie(name: str) -> dict[str, str | int] | None:
    """Match movie name pattern using walrus operator."""
    for pattern in MOVIE_PATTERNS:
        if match := re.match(pattern, name, re.IGNORECASE):
            groups = match.groups()
            if len(groups) >= 2:
                return {"title": groups[0].strip(), "year": int(groups[1])}
            elif len(groups) == 1:
                return {"title": groups[0].strip()}
    return None


def match_tv_series(name: str) -> dict[str, str] | None:
    """Match TV series name pattern."""
    for pattern in TV_PATTERNS:
        if match := re.match(pattern, name, re.IGNORECASE):
            groups = match.groups()
            if groups:
                return {"title": groups[0].strip()}
    return None


def match_episode(filename: str) -> dict[str, int] | None:
    """Match episode pattern using walrus operator."""
    for pattern in EPISODE_PATTERNS:
        if match := re.search(pattern, filename, re.IGNORECASE):
            groups = match.groups()
            if len(groups) >= 2:
                return {"season": int(groups[0]), "episode": int(groups[1])}
    return None


def match_season(dirname: str) -> dict[str, int] | None:
    """Match season pattern."""
    # Special case for specials
    if re.match(r"Specials?", dirname, re.IGNORECASE):
        return {"season": 0}

    for pattern in SEASON_PATTERNS:
        if match := re.search(pattern, dirname, re.IGNORECASE):
            groups = match.groups()
            if groups and groups[0].isdigit():
                return {"season": int(groups[0])}
    return None


def is_excluded(path: Path | str) -> bool:
    """Check if path should be excluded using any() with generator."""
    name = path.name if isinstance(path, Path) else str(path)

    # Using any() with generator expression for efficiency
    return any(exclusion in name or name.startswith(exclusion) for exclusion in DEFAULT_EXCLUSIONS)


def get_file_patterns() -> dict[str, list[str]]:
    """Get all file patterns as a dictionary."""
    return {
        "movie": MOVIE_PATTERNS,
        "tv": TV_PATTERNS,
        "episode": EPISODE_PATTERNS,
        "season": SEASON_PATTERNS,
        "exclusions": DEFAULT_EXCLUSIONS,
    }
