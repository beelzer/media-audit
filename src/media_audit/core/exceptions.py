"""Domain exceptions for media audit."""

from __future__ import annotations

from pathlib import Path


class MediaAuditError(Exception):
    """Base exception for media audit."""


class ConfigurationError(MediaAuditError):
    """Raised when configuration is invalid."""


class ScanError(MediaAuditError):
    """Raised when scanning fails."""


class ParseError(MediaAuditError):
    """Raised when parsing media files fails."""

    def __init__(self, path: Path, message: str) -> None:
        """Initialize with path and message."""
        self.path = path
        super().__init__(f"Failed to parse {path}: {message}")


class ValidationError(MediaAuditError):
    """Raised when validation fails."""


class ProbeError(MediaAuditError):
    """Raised when probing media files fails."""

    def __init__(self, path: Path, message: str) -> None:
        """Initialize with path and message."""
        self.path = path
        super().__init__(f"Failed to probe {path}: {message}")


class CacheError(MediaAuditError):
    """Raised when cache operations fail."""
