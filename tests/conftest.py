"""
Pytest configuration and shared fixtures for media-audit tests.
"""

import asyncio
import logging
import shutil
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
import pytest_asyncio

from media_audit.core.enums import CodecType, ValidationStatus
from media_audit.core.models import MediaAssets, ValidationIssue, VideoInfo
from media_audit.infrastructure.config.config import ScanConfig


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_config(temp_dir: Path) -> ScanConfig:
    """Create a mock configuration for testing."""
    from media_audit.core.enums import CodecType

    return ScanConfig(
        root_paths=[temp_dir],
        profiles=["all"],
        allowed_codecs=[CodecType.HEVC, CodecType.H264, CodecType.AV1],
        include_patterns=["*.mkv", "*.mp4", "*.avi"],
        exclude_patterns=["node_modules", ".git"],
        concurrent_workers=2,
        cache_enabled=True,
        cache_dir=temp_dir / ".cache",
    )


@pytest.fixture
def sample_video_info(temp_dir: Path) -> VideoInfo:
    """Create a sample video info for testing."""
    video_path = temp_dir / "sample_movie.mkv"
    video_path.touch()

    return VideoInfo(
        path=video_path,
        codec=CodecType.H264,
        resolution=(1920, 1080),
        duration=7200.0,
        bitrate=5000000,
        size=5368709120,
        frame_rate=23.976,
        audio_codec="aac",
        audio_channels=2,
        audio_bitrate=256000,
    )


@pytest.fixture
def sample_media_assets(temp_dir: Path) -> MediaAssets:
    """Create sample media assets for testing."""
    poster_path = temp_dir / "poster.jpg"
    poster_path.touch()

    nfo_path = temp_dir / "movie.nfo"
    nfo_path.touch()

    return MediaAssets(
        posters=[poster_path],
        nfo_files=[nfo_path],
    )


@pytest.fixture
def sample_validation_issue() -> ValidationIssue:
    """Create a sample validation issue for testing."""
    return ValidationIssue(
        category="quality",
        message="Low bitrate detected",
        severity=ValidationStatus.WARNING,
        details={"bitrate": 3000000, "expected": 5000000},
    )


@pytest.fixture
def mock_ffprobe() -> Mock:
    """Create a mock ffprobe command."""
    mock = Mock()
    mock.return_value = {
        "format": {
            "filename": "test.mkv",
            "format_name": "matroska,webm",
            "duration": "7200.000000",
            "size": "5368709120",
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
    return mock


@pytest_asyncio.fixture
async def async_mock_ffprobe() -> AsyncMock:
    """Create an async mock ffprobe command."""
    mock = AsyncMock()
    mock.return_value = {
        "format": {
            "filename": "test.mkv",
            "format_name": "matroska,webm",
            "duration": "7200.000000",
            "size": "5368709120",
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
    return mock


@pytest.fixture
def create_test_files(temp_dir: Path):
    """Factory fixture to create test media files."""

    def _create_files(count: int = 5, extensions: list[str] | None = None) -> list[Path]:
        if extensions is None:
            extensions = [".mkv", ".mp4", ".avi"]

        files = []
        for i in range(count):
            ext = extensions[i % len(extensions)]
            file_path = temp_dir / f"test_file_{i}{ext}"
            file_path.touch()
            files.append(file_path)

        return files

    return _create_files


@pytest.fixture
def mock_cache() -> MagicMock:
    """Create a mock cache for testing."""
    cache = MagicMock()
    cache.get = MagicMock(return_value=None)
    cache.set = MagicMock()
    cache.clear = MagicMock()
    cache.exists = MagicMock(return_value=False)
    return cache


@pytest.fixture
def mock_logger() -> MagicMock:
    """Create a mock logger for testing."""
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.critical = MagicMock()
    return logger


class MockProgressBar:
    """Mock progress bar for testing."""

    def __init__(self):
        self.total = 0
        self.current = 0
        self.description = ""

    def update(self, advance: int = 1):
        self.current += advance

    def set_description(self, description: str):
        self.description = description

    def close(self):
        pass


@pytest.fixture
def mock_progress() -> MockProgressBar:
    """Create a mock progress bar for testing."""
    return MockProgressBar()


@pytest.fixture
def sample_patterns() -> dict[str, list[str]]:
    """Sample patterns for testing."""
    return {
        "movie": [
            r"(?P<title>.+?)\.(?P<year>\d{4})\.(?P<resolution>\d+p)?\.?(?P<quality>BluRay|WEB-DL|WEBRip)?",
            r"(?P<title>.+?)\s*\((?P<year>\d{4})\)",
        ],
        "tv": [
            r"(?P<series>.+?)\.S(?P<season>\d{2})E(?P<episode>\d{2})",
            r"(?P<series>.+?)\s+(?P<season>\d+)x(?P<episode>\d{2})",
        ],
    }


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Reset any singleton instances if needed
    # Currently no singletons to reset
    yield


@pytest.fixture
def caplog_debug(caplog):
    """Set log capture to DEBUG level."""
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture
def suppress_output():
    """Suppress stdout/stderr during tests."""
    import io

    original_stdout = sys.stdout
    original_stderr = sys.stderr

    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    yield

    sys.stdout = original_stdout
    sys.stderr = original_stderr


@pytest.fixture
def benchmark():
    """Provide benchmark utility."""
    from tests.utils.benchmarks import Benchmark

    return Benchmark()


@pytest.fixture
def test_data_manager(temp_dir: Path):
    """Provide test data manager."""
    from tests.utils.fixtures import TestDataManager

    return TestDataManager(temp_dir)


@pytest.fixture
def media_library_builder(temp_dir: Path):
    """Provide media library builder."""
    from tests.utils.fixtures import MediaFileBuilder

    return MediaFileBuilder(temp_dir)


@pytest.fixture
def patch_manager():
    """Provide patch manager for multiple mocks."""
    from tests.utils.helpers import PatchManager

    manager = PatchManager()
    yield manager
    manager.stop_all()


@pytest.fixture
def async_runner():
    """Provide async test runner."""
    from tests.utils.helpers import AsyncTestRunner

    return AsyncTestRunner()


@pytest.fixture(scope="session")
def performance_baseline():
    """Store performance baselines for comparison."""
    return {
        "file_scan": 0.1,  # 100ms per file
        "pattern_match": 0.001,  # 1ms per pattern
        "cache_lookup": 0.0001,  # 0.1ms per lookup
    }
