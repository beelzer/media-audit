"""
Unit tests for core models.
"""

from pathlib import Path

from tests.utils.assertions import ValueAssertions
from tests.utils.factories import MediaAssetsFactory, ValidationIssueFactory, VideoInfoFactory

from media_audit.core.enums import CodecType, ValidationStatus
from media_audit.core.models import MediaAssets


class TestVideoInfo:
    """Tests for VideoInfo model."""

    def test_create_video_info(self, temp_dir: Path):
        """Test creating a video info with valid data."""
        video_path = temp_dir / "test.mkv"
        video_path.touch()

        video = VideoInfoFactory.create(path=video_path)

        assert video.path == video_path
        assert video.codec == CodecType.H264
        assert video.resolution == (1920, 1080)
        ValueAssertions.assert_close_to(video.frame_rate, 23.976, tolerance=0.001)
        assert video.bitrate == 5000000

    def test_video_info_with_custom_values(self, temp_dir: Path):
        """Test creating video info with custom values."""
        video_path = temp_dir / "4k_video.mkv"
        video_path.touch()

        video = VideoInfoFactory.create(
            path=video_path,
            codec=CodecType.HEVC,
            resolution=(3840, 2160),
            frame_rate=60.0,
            bitrate=20000000,
        )

        assert video.codec == CodecType.HEVC
        assert video.resolution == (3840, 2160)
        assert video.frame_rate == 60.0
        assert video.bitrate == 20000000

    def test_is_high_quality(self, temp_dir: Path):
        """Test high quality detection."""
        # Test 4K video
        video_4k = VideoInfoFactory.create(
            path=temp_dir / "4k.mkv", resolution=(3840, 2160), bitrate=20000000
        )
        assert video_4k.is_high_quality is True

        # Test 1080p with good bitrate
        video_1080p_good = VideoInfoFactory.create(
            path=temp_dir / "1080p_good.mkv", resolution=(1920, 1080), bitrate=8000000
        )
        assert video_1080p_good.is_high_quality is True

        # Test 1080p with low bitrate
        video_1080p_low = VideoInfoFactory.create(
            path=temp_dir / "1080p_low.mkv", resolution=(1920, 1080), bitrate=3000000
        )
        assert video_1080p_low.is_high_quality is False

        # Test 720p
        video_720p = VideoInfoFactory.create(
            path=temp_dir / "720p.mkv", resolution=(1280, 720), bitrate=5000000
        )
        assert video_720p.is_high_quality is False

    def test_video_info_batch_creation(self, temp_dir: Path):
        """Test creating multiple video infos."""
        videos = VideoInfoFactory.create_batch(count=5, base_path=temp_dir)

        assert len(videos) == 5
        for i, video in enumerate(videos):
            assert video.path == temp_dir / f"video_{i}.mkv"
            assert video.codec == CodecType.H264


class TestMediaAssets:
    """Tests for MediaAssets model."""

    def test_create_media_assets(self, temp_dir: Path):
        """Test creating media assets with defaults."""
        assets = MediaAssetsFactory.create(base_path=temp_dir)

        assert len(assets.posters) == 1
        assert assets.posters[0] == temp_dir / "poster.jpg"
        assert len(assets.nfo_files) == 1
        assert assets.nfo_files[0] == temp_dir / "movie.nfo"

    def test_create_full_media_assets(self, temp_dir: Path):
        """Test creating media assets with all types."""
        assets = MediaAssetsFactory.create_full(base_path=temp_dir)

        assert len(assets.posters) == 2
        assert len(assets.backgrounds) == 1
        assert len(assets.banners) == 1
        assert len(assets.logos) == 1
        assert len(assets.trailers) == 1
        assert len(assets.title_cards) == 1
        assert len(assets.subtitles) == 2
        assert len(assets.nfo_files) == 1

    def test_has_minimal_assets(self, temp_dir: Path):
        """Test minimal assets detection."""
        # With poster
        assets_with_poster = MediaAssets(posters=[temp_dir / "poster.jpg"])
        assert assets_with_poster.has_minimal_assets() is True

        # With NFO
        assets_with_nfo = MediaAssets(nfo_files=[temp_dir / "movie.nfo"])
        assert assets_with_nfo.has_minimal_assets() is True

        # Without minimal assets
        assets_empty = MediaAssets()
        assert assets_empty.has_minimal_assets() is False

    def test_all_assets(self, temp_dir: Path):
        """Test getting all assets as flat list."""
        assets = MediaAssetsFactory.create_full(base_path=temp_dir)
        all_assets = assets.all_assets()

        # Should include all files from all categories
        assert len(all_assets) == 10  # 2+1+1+1+1+1+2+1


class TestValidationIssue:
    """Tests for ValidationIssue model."""

    def test_create_validation_issue(self):
        """Test creating a validation issue."""
        issue = ValidationIssueFactory.create()

        assert issue.category == "quality"
        assert issue.message == "Issue detected"
        assert issue.severity == ValidationStatus.WARNING
        assert issue.details == {}

    def test_validation_issue_with_details(self):
        """Test validation issue with custom details."""
        issue = ValidationIssueFactory.create(
            category="bitrate",
            message="Low bitrate detected",
            severity=ValidationStatus.ERROR,
            details={"actual": 3000000, "expected": 5000000, "file": "test.mkv"},
        )

        assert issue.category == "bitrate"
        assert issue.severity == ValidationStatus.ERROR
        assert issue.details["actual"] == 3000000
        assert issue.details["expected"] == 5000000

    def test_validation_issue_to_dict(self):
        """Test converting validation issue to dict."""
        issue = ValidationIssueFactory.create(
            severity=ValidationStatus.ERROR, details={"test": "value"}
        )

        issue_dict = issue.to_dict()

        assert issue_dict["category"] == "quality"
        assert issue_dict["message"] == "Issue detected"
        assert issue_dict["severity"] == "error"
        assert issue_dict["details"] == {"test": "value"}

    def test_validation_issue_batch_creation(self):
        """Test creating multiple validation issues."""
        issues = ValidationIssueFactory.create_batch(
            count=6,
            severities=[ValidationStatus.WARNING, ValidationStatus.ERROR, ValidationStatus.VALID],
        )

        assert len(issues) == 6

        # Check severity cycling
        assert issues[0].severity == ValidationStatus.WARNING
        assert issues[1].severity == ValidationStatus.ERROR
        assert issues[2].severity == ValidationStatus.VALID
        assert issues[3].severity == ValidationStatus.WARNING

        # Check category cycling
        categories = [issue.category for issue in issues]
        assert "quality" in categories
        assert "naming" in categories
        assert "metadata" in categories
