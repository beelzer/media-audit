"""Tests for ffprobe module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from media_audit.core import CodecType, VideoInfo
from media_audit.infrastructure.probe.ffprobe import FFProbe, probe_video


@pytest.fixture
def ffprobe_instance():
    """Create FFProbe instance."""
    with patch("media_audit.infrastructure.probe.ffprobe.shutil.which") as mock_which:
        mock_which.return_value = "/usr/bin/ffprobe"
        return FFProbe()


@pytest.fixture
def mock_ffprobe_output():
    """Mock ffprobe JSON output."""
    return {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "hevc",
                "width": 1920,
                "height": 1080,
                "bit_rate": "8000000",
                "duration": "7200.5",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
            },
        ],
        "format": {
            "size": "7200000000",
            "bit_rate": "8000000",
            "duration": "7200.5",
        },
    }


def test_ffprobe_available():
    """Test checking if ffprobe is available."""
    with patch("media_audit.infrastructure.probe.ffprobe.shutil.which") as mock_which:
        mock_which.return_value = "/usr/bin/ffprobe"
        ffprobe = FFProbe()
        assert ffprobe.ffprobe_path == "/usr/bin/ffprobe"

    with patch("media_audit.infrastructure.probe.ffprobe.shutil.which") as mock_which:
        mock_which.return_value = None
        with pytest.raises(RuntimeError, match="ffprobe not found"):
            FFProbe()


def test_parse_codec_type():
    """Test parsing codec type from string."""
    with patch("media_audit.infrastructure.probe.ffprobe.shutil.which") as mock_which:
        mock_which.return_value = "/usr/bin/ffprobe"
        ffprobe = FFProbe()

    assert ffprobe._map_codec("hevc") == CodecType.HEVC
    assert ffprobe._map_codec("h265") == CodecType.H265
    assert ffprobe._map_codec("h264") == CodecType.H264
    assert ffprobe._map_codec("av1") == CodecType.AV1
    assert ffprobe._map_codec("vp9") == CodecType.VP9
    assert ffprobe._map_codec("mpeg4") == CodecType.MPEG4
    assert ffprobe._map_codec("mpeg2video") == CodecType.MPEG2
    assert ffprobe._map_codec("unknown") == CodecType.UNKNOWN


@pytest.mark.asyncio
async def test_probe_success(ffprobe_instance, mock_ffprobe_output):
    """Test successful video probing."""
    with patch("media_audit.infrastructure.probe.ffprobe.FFProbe.probe") as mock_probe:
        mock_probe.return_value = mock_ffprobe_output

        video_info = await ffprobe_instance.get_video_info(Path("/test/video.mkv"))

        assert video_info is not None
        assert video_info.codec == CodecType.HEVC
        assert video_info.resolution == (1920, 1080)
        assert video_info.duration == 7200.5
        assert video_info.bitrate == 8000000
        assert video_info.size == 7200000000


@pytest.mark.asyncio
async def test_probe_file_not_found(ffprobe_instance):
    """Test probing non-existent file."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError

        raw_data = await ffprobe_instance.probe(Path("/nonexistent/video.mkv"))
        assert raw_data == {}


@pytest.mark.asyncio
async def test_probe_invalid_json(ffprobe_instance):
    """Test handling invalid JSON from ffprobe."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="invalid json", stderr="")

        raw_data = await ffprobe_instance.probe(Path("/test/video.mkv"))
        assert raw_data == {}


@pytest.mark.asyncio
async def test_probe_no_video_stream(ffprobe_instance):
    """Test probing file with no video stream."""
    output = {
        "streams": [
            {
                "codec_type": "audio",
                "codec_name": "aac",
            }
        ],
        "format": {
            "size": "1000000",
        },
    }

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(output), stderr="")

        video_info = await ffprobe_instance.get_video_info(Path("/test/audio.mp3"))
        assert video_info is not None
        assert video_info.codec is None
        assert video_info.resolution is None


@pytest.mark.asyncio
async def test_probe_missing_fields(ffprobe_instance):
    """Test probing with missing fields in output."""
    output = {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                # Missing width, height, duration, etc.
            }
        ],
        "format": {},  # Missing all fields
    }

    with patch("media_audit.infrastructure.probe.ffprobe.FFProbe.probe") as mock_probe:
        mock_probe.return_value = output

        video_info = await ffprobe_instance.get_video_info(Path("/test/video.mp4"))
        assert video_info is not None
        assert video_info.codec == CodecType.H264
        assert video_info.resolution is None
        assert video_info.duration == 0
        assert video_info.bitrate == 0


@pytest.mark.asyncio
async def test_probe_video_function():
    """Test the probe_video convenience function."""
    with patch("media_audit.infrastructure.probe.ffprobe.shutil.which") as mock_which:
        mock_which.return_value = "/usr/bin/ffprobe"
        with patch(
            "media_audit.infrastructure.probe.ffprobe.FFProbe.get_video_info"
        ) as mock_get_video_info:
            # Make the mock async
            async def async_get_video_info(path):
                return VideoInfo(
                    path=Path("/test/video.mkv"),
                    codec=CodecType.HEVC,
                    resolution=(1920, 1080),
                )

            mock_get_video_info.side_effect = async_get_video_info

            result = await probe_video(Path("/test/video.mkv"))
            assert result is not None
            assert result.codec == CodecType.HEVC
            mock_get_video_info.assert_called_once_with(Path("/test/video.mkv"))


@pytest.mark.asyncio
async def test_probe_command_construction(ffprobe_instance):
    """Test that ffprobe command is constructed correctly."""
    with patch("asyncio.create_subprocess_exec") as mock_create:
        # Create a mock process
        mock_process = MagicMock()

        # Make communicate async
        async def communicate():
            return (json.dumps({"streams": [], "format": {}}).encode(), b"")

        mock_process.communicate = communicate
        mock_process.returncode = 0

        # Make create_subprocess_exec return the mock process
        async def async_create(*args, **kwargs):
            return mock_process

        mock_create.side_effect = async_create

        await ffprobe_instance.probe(Path("/test/video.mkv"))

        # Check the command was constructed correctly
        call_args = mock_create.call_args[0]
        assert ffprobe_instance.ffprobe_path in call_args[0]
        assert "-v" in call_args
        assert "quiet" in call_args
        assert "-print_format" in call_args
        assert "json" in call_args
        assert "-show_format" in call_args
        assert "-show_streams" in call_args
        assert str(Path("/test/video.mkv")) in call_args
