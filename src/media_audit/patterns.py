"""Pattern definitions for different media server types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Pattern
import re


@dataclass
class MediaPatterns:
    """Collection of patterns for matching media files."""

    poster_patterns: list[str] = field(default_factory=list)
    background_patterns: list[str] = field(default_factory=list)
    banner_patterns: list[str] = field(default_factory=list)
    trailer_patterns: list[str] = field(default_factory=list)
    title_card_patterns: list[str] = field(default_factory=list)

    def compile_patterns(self) -> CompiledPatterns:
        """Compile regex patterns for efficient matching."""
        return CompiledPatterns(
            poster_re=[re.compile(p, re.IGNORECASE) for p in self.poster_patterns],
            background_re=[re.compile(p, re.IGNORECASE) for p in self.background_patterns],
            banner_re=[re.compile(p, re.IGNORECASE) for p in self.banner_patterns],
            trailer_re=[re.compile(p, re.IGNORECASE) for p in self.trailer_patterns],
            title_card_re=[re.compile(p, re.IGNORECASE) for p in self.title_card_patterns],
        )


@dataclass
class CompiledPatterns:
    """Compiled regex patterns for matching."""

    poster_re: list[Pattern[str]] = field(default_factory=list)
    background_re: list[Pattern[str]] = field(default_factory=list)
    banner_re: list[Pattern[str]] = field(default_factory=list)
    trailer_re: list[Pattern[str]] = field(default_factory=list)
    title_card_re: list[Pattern[str]] = field(default_factory=list)


# Plex patterns
PLEX_PATTERNS = MediaPatterns(
    poster_patterns=[
        r"^poster\.",
        r"^folder\.",
        r"^movie\.",
        r"^cover\.",
        r"^default\.",
        r"^poster-\d+\.",
    ],
    background_patterns=[
        r"^fanart\.",
        r"^background\.",
        r"^backdrop\.",
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
)

# Jellyfin patterns
JELLYFIN_PATTERNS = MediaPatterns(
    poster_patterns=[
        r"^poster\.",
        r"^folder\.",
        r"^cover\.",
        r"^poster-\d+\.",
        r"^poster\d+\.",
    ],
    background_patterns=[
        r"^backdrop\.",
        r"^fanart\.",
        r"^background\.",
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
        r".*\.trailer\.",
    ],
    title_card_patterns=[
        r"^S\d{2}E\d{2}\.",
        r"^S\d{2}E\d{2}-thumb\.",
        r"^episode-S\d{2}E\d{2}\.",
    ],
)

# Emby patterns
EMBY_PATTERNS = MediaPatterns(
    poster_patterns=[
        r"^folder\.",
        r"^poster\.",
        r"^cover\.",
        r"^movie\.",
        r"^poster-\d+\.",
    ],
    background_patterns=[
        r"^backdrop\.",
        r"^fanart\.",
        r"^background\.",
        r"^backdrop\d+\.",
        r"^backdrop-\d+\.",
        r"^extrafanart/.*",
    ],
    banner_patterns=[
        r"^banner\.",
        r"^banner-\d+\.",
    ],
    trailer_patterns=[
        r"-trailer\.",
        r"^trailers/.*",
        r".*-trailer\.",
    ],
    title_card_patterns=[
        r"^S\d{2}E\d{2}\.",
        r"^S\d{2}E\d{2}-thumb\.",
        r"^episode-S\d{2}E\d{2}\.",
    ],
)

# Combined patterns (union of all)
COMBINED_PATTERNS = MediaPatterns(
    poster_patterns=list(
        set(PLEX_PATTERNS.poster_patterns)
        | set(JELLYFIN_PATTERNS.poster_patterns)
        | set(EMBY_PATTERNS.poster_patterns)
    ),
    background_patterns=list(
        set(PLEX_PATTERNS.background_patterns)
        | set(JELLYFIN_PATTERNS.background_patterns)
        | set(EMBY_PATTERNS.background_patterns)
    ),
    banner_patterns=list(
        set(PLEX_PATTERNS.banner_patterns)
        | set(JELLYFIN_PATTERNS.banner_patterns)
        | set(EMBY_PATTERNS.banner_patterns)
    ),
    trailer_patterns=list(
        set(PLEX_PATTERNS.trailer_patterns)
        | set(JELLYFIN_PATTERNS.trailer_patterns)
        | set(EMBY_PATTERNS.trailer_patterns)
    ),
    title_card_patterns=list(
        set(PLEX_PATTERNS.title_card_patterns)
        | set(JELLYFIN_PATTERNS.title_card_patterns)
        | set(EMBY_PATTERNS.title_card_patterns)
    ),
)


PATTERN_PRESETS = {
    "plex": PLEX_PATTERNS,
    "jellyfin": JELLYFIN_PATTERNS,
    "emby": EMBY_PATTERNS,
    "all": COMBINED_PATTERNS,
}


def get_patterns(profiles: list[str] | None = None) -> MediaPatterns:
    """Get combined patterns for specified profiles."""
    if not profiles:
        return COMBINED_PATTERNS

    all_patterns = MediaPatterns(
        poster_patterns=[],
        background_patterns=[],
        banner_patterns=[],
        trailer_patterns=[],
        title_card_patterns=[],
    )

    for profile in profiles:
        if profile.lower() in PATTERN_PRESETS:
            preset = PATTERN_PRESETS[profile.lower()]
            all_patterns.poster_patterns.extend(preset.poster_patterns)
            all_patterns.background_patterns.extend(preset.background_patterns)
            all_patterns.banner_patterns.extend(preset.banner_patterns)
            all_patterns.trailer_patterns.extend(preset.trailer_patterns)
            all_patterns.title_card_patterns.extend(preset.title_card_patterns)

    # Remove duplicates
    all_patterns.poster_patterns = list(set(all_patterns.poster_patterns))
    all_patterns.background_patterns = list(set(all_patterns.background_patterns))
    all_patterns.banner_patterns = list(set(all_patterns.banner_patterns))
    all_patterns.trailer_patterns = list(set(all_patterns.trailer_patterns))
    all_patterns.title_card_patterns = list(set(all_patterns.title_card_patterns))

    return all_patterns