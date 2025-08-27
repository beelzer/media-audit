"""FFprobe integration for video analysis."""

from __future__ import annotations

import json
import shutil
import subprocess
from functools import cache
from pathlib import Path
from typing import Any

from media_audit.cache import MediaCache
from media_audit.models import CodecType, VideoInfo


class FFProbe:
    """FFprobe wrapper for video analysis."""

    def __init__(self, ffprobe_path: str | None = None, cache: MediaCache | None = None):
        """Initialize FFProbe."""
        self.ffprobe_path: str = ffprobe_path or self._find_ffprobe() or ""
        if not self.ffprobe_path:
            raise RuntimeError("ffprobe not found. Please install ffmpeg.")
        self.cache = cache

    @staticmethod
    def _find_ffprobe() -> str | None:
        """Find ffprobe in system PATH."""
        return shutil.which("ffprobe")

    def probe(self, file_path: Path) -> dict[str, Any]:
        """Probe a video file for metadata."""
        # Check cache first
        if self.cache:
            cached_data = self.cache.get_probe_data(file_path)
            if cached_data is not None:
                return cached_data

        # Probe the file
        cmd = [
            self.ffprobe_path,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, encoding="utf-8", errors="replace"
            )
            data = json.loads(result.stdout)

            # Cache the result
            if self.cache and data:
                self.cache.set_probe_data(file_path, data)

            return data  # type: ignore[no-any-return]
        except subprocess.CalledProcessError as e:
            # Log specific ffprobe error if available
            if e.stderr:
                import logging

                logging.getLogger("media_audit.probe").warning(
                    f"FFprobe error for {file_path}: {e.stderr}"
                )
            return {}
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def get_video_info(self, file_path: Path) -> VideoInfo:
        """Extract video information from file."""
        info = VideoInfo(path=file_path)

        try:
            data = self.probe(file_path)
            info.raw_info = data

            # Get format info
            if "format" in data:
                format_data = data["format"]
                info.duration = float(format_data.get("duration", 0))
                info.bitrate = int(format_data.get("bit_rate", 0))
                info.size = int(format_data.get("size", 0))

            # Find video stream
            video_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break

            if video_stream:
                # Extract codec
                codec_name = video_stream.get("codec_name", "").lower()
                info.codec = self._map_codec(codec_name)

                # Extract resolution
                width = video_stream.get("width")
                height = video_stream.get("height")
                if width and height:
                    info.resolution = (int(width), int(height))

        except Exception as e:
            # Log unexpected errors
            import logging

            logging.getLogger("media_audit.probe").debug(
                f"Unexpected error probing {file_path}: {e}"
            )

        return info

    @staticmethod
    def _map_codec(codec_name: str) -> CodecType:
        """Map codec name to CodecType using pattern matching."""
        # Use match/case for cleaner codec mapping (Python 3.10+)
        match codec_name:
            case name if "hevc" in name:
                return CodecType.HEVC
            case name if "h265" in name:
                return CodecType.H265
            case name if "av1" in name:
                return CodecType.AV1
            case name if "h264" in name or "avc" in name:
                return CodecType.H264
            case name if "vp9" in name:
                return CodecType.VP9
            case name if "mpeg4" in name:
                return CodecType.MPEG4
            case name if "mpeg2" in name:
                return CodecType.MPEG2
            case _:
                return CodecType.UNKNOWN


@cache
def _get_default_probe() -> FFProbe:
    """Get default FFProbe instance (singleton)."""
    return FFProbe()


def probe_video(file_path: Path, cache: MediaCache | None = None) -> VideoInfo:
    """Probe a video file using FFProbe instance."""
    if cache:
        probe = FFProbe(cache=cache)
        return probe.get_video_info(file_path)
    else:
        return _get_default_probe().get_video_info(file_path)
