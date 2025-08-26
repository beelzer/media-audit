"""FFprobe integration for video analysis."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any
from functools import lru_cache

from ..models import CodecType, VideoInfo


class FFProbe:
    """FFprobe wrapper for video analysis."""

    def __init__(self, ffprobe_path: str | None = None):
        """Initialize FFProbe."""
        self.ffprobe_path = ffprobe_path or self._find_ffprobe()
        if not self.ffprobe_path:
            raise RuntimeError("ffprobe not found. Please install ffmpeg.")

    @staticmethod
    def _find_ffprobe() -> str | None:
        """Find ffprobe in system PATH."""
        return shutil.which("ffprobe")

    def probe(self, file_path: Path) -> dict[str, Any]:
        """Probe a video file for metadata."""
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
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

        except Exception:
            # Return partial info on error
            pass

        return info

    @staticmethod
    def _map_codec(codec_name: str) -> CodecType:
        """Map codec name to CodecType."""
        codec_map = {
            "hevc": CodecType.HEVC,
            "h265": CodecType.H265,
            "av1": CodecType.AV1,
            "h264": CodecType.H264,
            "vp9": CodecType.VP9,
            "mpeg4": CodecType.MPEG4,
            "mpeg2video": CodecType.MPEG2,
        }

        for key, value in codec_map.items():
            if key in codec_name:
                return value

        return CodecType.OTHER


@lru_cache(maxsize=1)
def _get_default_probe() -> FFProbe:
    """Get default FFProbe instance."""
    return FFProbe()


def probe_video(file_path: Path) -> VideoInfo:
    """Probe a video file using default FFProbe instance."""
    return _get_default_probe().get_video_info(file_path)