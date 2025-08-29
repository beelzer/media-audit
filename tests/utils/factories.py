"""
Factory classes for creating test objects dynamically.
"""

from pathlib import Path
from typing import Any

from media_audit.core.enums import CodecType, ValidationStatus
from media_audit.core.models import MediaAssets, ValidationIssue, VideoInfo
from media_audit.infrastructure.config.config import ScanConfig


class VideoInfoFactory:
    """Factory for creating VideoInfo objects."""

    @staticmethod
    def create(path: Path | str | None = None, **overrides) -> VideoInfo:
        """Create a video info with sensible defaults."""
        if path is None:
            path = Path("/test/video.mkv")
        elif isinstance(path, str):
            path = Path(path)

        defaults = {
            "path": path,
            "codec": CodecType.H264,
            "resolution": (1920, 1080),
            "duration": 7200.0,
            "bitrate": 5000000,
            "size": 5368709120,
            "frame_rate": 23.976,
            "audio_codec": "aac",
            "audio_channels": 2,
            "audio_bitrate": 256000,
        }
        return VideoInfo(**{**defaults, **overrides})

    @staticmethod
    def create_batch(count: int = 5, base_path: Path | None = None) -> list[VideoInfo]:
        """Create multiple video infos."""
        videos = []
        for i in range(count):
            path = (base_path or Path("/test")) / f"video_{i}.mkv"
            videos.append(VideoInfoFactory.create(path))
        return videos


class MediaAssetsFactory:
    """Factory for creating MediaAssets objects."""

    @staticmethod
    def create(base_path: Path | None = None, **overrides) -> MediaAssets:
        """Create media assets with flexible configuration."""
        if base_path is None:
            base_path = Path("/test/media")

        defaults = {
            "posters": [base_path / "poster.jpg"],
            "backgrounds": [],
            "banners": [],
            "logos": [],
            "trailers": [],
            "title_cards": [],
            "subtitles": [],
            "nfo_files": [base_path / "movie.nfo"],
        }

        return MediaAssets(**{**defaults, **overrides})

    @staticmethod
    def create_full(base_path: Path | None = None) -> MediaAssets:
        """Create media assets with all types populated."""
        if base_path is None:
            base_path = Path("/test/media")

        return MediaAssets(
            posters=[base_path / "poster.jpg", base_path / "poster2.jpg"],
            backgrounds=[base_path / "background.jpg"],
            banners=[base_path / "banner.jpg"],
            logos=[base_path / "logo.png"],
            trailers=[base_path / "trailer.mp4"],
            title_cards=[base_path / "titlecard.jpg"],
            subtitles=[base_path / "movie.en.srt", base_path / "movie.fr.srt"],
            nfo_files=[base_path / "movie.nfo"],
        )


class ValidationIssueFactory:
    """Factory for creating ValidationIssue objects."""

    @staticmethod
    def create(**overrides) -> ValidationIssue:
        """Create a validation issue with defaults."""
        defaults = {
            "category": "quality",
            "message": "Issue detected",
            "severity": ValidationStatus.WARNING,
            "details": {},
        }
        return ValidationIssue(**{**defaults, **overrides})

    @staticmethod
    def create_batch(
        count: int = 5, severities: list[ValidationStatus] | None = None
    ) -> list[ValidationIssue]:
        """Create multiple validation issues."""
        if severities is None:
            severities = [ValidationStatus.WARNING, ValidationStatus.ERROR]

        issues = []
        categories = ["quality", "naming", "metadata", "codec"]

        for i in range(count):
            issue = ValidationIssueFactory.create(
                category=categories[i % len(categories)],
                message=f"Issue {i + 1} detected",
                severity=severities[i % len(severities)],
                details={"index": i},
            )
            issues.append(issue)

        return issues


class ConfigFactory:
    """Factory for creating ScanConfig objects."""

    @staticmethod
    def create(base_path: Path | None = None, **overrides) -> ScanConfig:
        """Create a config with flexible settings."""
        from media_audit.core.enums import CodecType

        if base_path is None:
            base_path = Path("/test")

        defaults = {
            "root_paths": [base_path / "media"],
            "profiles": ["all"],
            "allowed_codecs": [CodecType.HEVC, CodecType.H264, CodecType.AV1],
            "include_patterns": ["*.mkv", "*.mp4", "*.avi"],
            "exclude_patterns": ["node_modules", ".git", "__pycache__"],
            "concurrent_workers": 4,
            "cache_enabled": True,
            "cache_dir": base_path / ".cache",
        }

        return ScanConfig(**{**defaults, **overrides})

    @staticmethod
    def minimal() -> ScanConfig:
        """Create a minimal config for simple tests."""
        return ScanConfig(
            root_paths=[Path("/test")],
            profiles=["all"],
            concurrent_workers=1,
            cache_enabled=False,
        )


class FFProbeDataFactory:
    """Factory for creating FFProbe output data."""

    @staticmethod
    def create_output(**overrides) -> dict[str, Any]:
        """Create FFProbe JSON output."""
        defaults = {
            "format": {
                "filename": "test.mkv",
                "format_name": "matroska,webm",
                "duration": "7200.000000",
                "size": "5368709120",
                "bit_rate": "5968343",
            },
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "codec_long_name": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10",
                    "width": 1920,
                    "height": 1080,
                    "display_aspect_ratio": "16:9",
                    "r_frame_rate": "24000/1001",
                    "bit_rate": "5000000",
                    "duration": "7200.000000",
                    "nb_frames": "172224",
                },
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "codec_long_name": "AAC (Advanced Audio Coding)",
                    "channels": 2,
                    "channel_layout": "stereo",
                    "sample_rate": "48000",
                    "bit_rate": "256000",
                    "duration": "7200.000000",
                    "tags": {"language": "eng"},
                },
            ],
        }

        return {**defaults, **overrides}

    @staticmethod
    def create_error_output() -> dict[str, Any]:
        """Create FFProbe output for error scenarios."""
        return {"error": {"code": -1, "string": "Invalid data found when processing input"}}
