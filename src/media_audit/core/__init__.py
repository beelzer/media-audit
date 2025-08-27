"""Core domain models and enums for media audit."""

from .enums import CodecType, MediaProfile, MediaSource, MediaType, ValidationStatus
from .exceptions import (
    CacheError,
    ConfigurationError,
    MediaAuditError,
    ParseError,
    ProbeError,
    ScanError,
    ValidationError,
)
from .models import (
    EpisodeItem,
    MediaAssets,
    MediaItem,
    MovieItem,
    ScanResult,
    SeasonItem,
    SeriesItem,
    ValidationIssue,
    VideoInfo,
)

__all__ = [
    # Enums
    "CodecType",
    "MediaProfile",
    "MediaSource",
    "MediaType",
    "ValidationStatus",
    # Exceptions
    "CacheError",
    "ConfigurationError",
    "MediaAuditError",
    "ParseError",
    "ProbeError",
    "ScanError",
    "ValidationError",
    # Models
    "EpisodeItem",
    "MediaAssets",
    "MediaItem",
    "MovieItem",
    "ScanResult",
    "SeasonItem",
    "SeriesItem",
    "ValidationIssue",
    "VideoInfo",
]
