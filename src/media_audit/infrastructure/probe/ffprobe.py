"""FFprobe integration for video analysis."""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
import sys
from contextlib import suppress
from functools import cache
from pathlib import Path
from typing import Any

from media_audit.core import CodecType, VideoInfo
from media_audit.infrastructure.cache import MediaCache


class FFProbe:
    """FFprobe wrapper for video analysis."""

    def __init__(self, ffprobe_path: str | None = None, cache: MediaCache | None = None):
        """Initialize FFProbe."""
        self.ffprobe_path: str = ffprobe_path or self._find_ffprobe() or ""
        if not self.ffprobe_path:
            raise RuntimeError("ffprobe not found. Please install ffmpeg.")
        self.cache = cache
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _find_ffprobe() -> str | None:
        """Find ffprobe in system PATH."""
        return shutil.which("ffprobe")

    async def probe(self, file_path: Path) -> dict[str, Any]:
        """Probe a video file for metadata."""
        # Check cache first
        if self.cache:
            cached_data = await self.cache.get_probe_data(file_path)
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

        proc = None
        try:
            # Create subprocess with proper cleanup
            # On Windows, prevent console window popup
            creation_flags = 0
            if sys.platform == "win32":
                # CREATE_NO_WINDOW is only available on Windows
                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=creation_flags,
            )

            # Set a timeout for the probe operation
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
            except TimeoutError:
                self.logger.warning(f"FFprobe timeout for {file_path}")
                if proc:
                    proc.terminate()
                    await asyncio.sleep(0.1)  # Give it a moment to terminate
                    if proc.returncode is None:
                        proc.kill()  # Force kill if still running
                return {}

            if proc.returncode != 0:
                if stderr:
                    import logging

                    logging.getLogger("media_audit.probe").warning(
                        f"FFprobe error for {file_path}: {stderr.decode('utf-8', errors='replace')}"
                    )
                return {}

            data = json.loads(stdout.decode("utf-8", errors="replace"))

            # Cache the result
            if self.cache and data:
                await self.cache.set_probe_data(file_path, data)

            return data  # type: ignore[no-any-return]
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.warning(f"Failed to probe {file_path}: {e}")
            return {}
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            if proc and proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=1.0)
                except TimeoutError:
                    proc.kill()
            raise  # Re-raise to propagate cancellation
        except Exception as e:
            self.logger.error(f"Unexpected error probing {file_path}: {e}", exc_info=True)
            return {}
        finally:
            # Ensure process is cleaned up
            if proc and proc.returncode is None:
                try:
                    proc.terminate()
                    await asyncio.wait_for(proc.wait(), timeout=0.5)
                except (TimeoutError, ProcessLookupError):
                    with suppress(ProcessLookupError):
                        proc.kill()

    async def get_video_info(self, file_path: Path) -> VideoInfo:
        """Extract video information from file."""
        info = VideoInfo(path=file_path)

        try:
            data = await self.probe(file_path)
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
            self.logger.debug(f"Failed to extract video info from {file_path}: {e}")

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


async def probe_video(file_path: Path, cache: MediaCache | None = None) -> VideoInfo:
    """Probe a video file using FFProbe instance."""
    probe = FFProbe(cache=cache) if cache else FFProbe()
    return await probe.get_video_info(file_path)
