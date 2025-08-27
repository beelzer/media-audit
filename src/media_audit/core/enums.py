"""Domain enums for media audit using Python 3.13 features."""

from __future__ import annotations

from enum import StrEnum
from typing import override


class MediaType(StrEnum):
    """Type of media content using StrEnum for better string handling."""

    MOVIE = "movie"
    TV_SERIES = "tv_series"
    TV_SEASON = "tv_season"
    TV_EPISODE = "tv_episode"
    UNKNOWN = "unknown"

    @override
    def __str__(self) -> str:
        """Return readable string representation."""
        return self.value.replace("_", " ").title()


class ValidationStatus(StrEnum):
    """Validation status for media items."""

    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"


class CodecType(StrEnum):
    """Video codec types using StrEnum."""

    HEVC = "hevc"
    AV1 = "av1"
    H264 = "h264"
    H265 = "h265"
    VP9 = "vp9"
    VP8 = "vp8"
    MPEG4 = "mpeg4"
    MPEG2 = "mpeg2"
    XVID = "xvid"
    DIVX = "divx"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, codec_str: str) -> CodecType:
        """Create CodecType from codec string using pattern matching.

        Args:
            codec_str: String representation of codec (e.g., "hevc", "h265", "x265")

        Returns:
            CodecType: Corresponding codec enum value, UNKNOWN if not recognized

        """
        if not codec_str:
            return cls.UNKNOWN

        codec_lower = codec_str.lower().strip()

        # Using match/case for cleaner codec mapping
        match codec_lower:
            case "hevc" | "h265" | "x265":
                return cls.HEVC
            case "h264" | "x264" | "avc":
                return cls.H264
            case "av1" | "av01":
                return cls.AV1
            case "vp9":
                return cls.VP9
            case "vp8":
                return cls.VP8
            case "mpeg4" | "mp4v":
                return cls.MPEG4
            case "mpeg2" | "mp2v":
                return cls.MPEG2
            case "xvid":
                return cls.XVID
            case "divx":
                return cls.DIVX
            case _:
                return cls.UNKNOWN


class MediaSource(StrEnum):
    """Media source types."""

    BLURAY = "bluray"
    WEB_DL = "web-dl"
    WEBRIP = "webrip"
    HDTV = "hdtv"
    DVD = "dvd"
    CAM = "cam"
    SCREENER = "screener"
    UNKNOWN = "unknown"


class MediaProfile(StrEnum):
    """Media server profiles."""

    PLEX = "plex"
    JELLYFIN = "jellyfin"
    EMBY = "emby"
    KODI = "kodi"
    ALL = "all"
