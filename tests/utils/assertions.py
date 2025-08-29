"""
Custom assertions and matchers for media-audit tests.
"""

from pathlib import Path
from typing import Any

from media_audit.core.models import MediaAssets, ValidationIssue, VideoInfo


class VideoInfoAssertions:
    """Assertions specific to VideoInfo objects."""

    @staticmethod
    def assert_valid_video_info(video: VideoInfo, strict: bool = False):
        """Assert that a video info has valid basic properties."""
        assert video.path, "Video must have a file path"
        assert video.size >= 0, "File size must be non-negative"

        if video.duration is not None:
            assert video.duration >= 0, "Duration must be non-negative"

        if video.bitrate is not None:
            assert video.bitrate >= 0, "Bitrate must be non-negative"

        if strict:
            assert video.codec is not None, "Video must have a codec"
            assert video.resolution is not None, "Video must have resolution"
            assert video.duration is not None, "Video must have duration"

    @staticmethod
    def assert_resolution_valid(video: VideoInfo):
        """Assert that video resolution is valid."""
        if video.resolution:
            width, height = video.resolution
            assert width > 0, "Video width must be positive"
            assert height > 0, "Video height must be positive"

    @staticmethod
    def assert_video_infos_equal(
        video1: VideoInfo, video2: VideoInfo, ignore_fields: list[str] | None = None
    ):
        """Assert that two video infos are equal, optionally ignoring certain fields."""
        if ignore_fields is None:
            ignore_fields = []

        for field in ["path", "codec", "resolution", "duration", "bitrate", "size"]:
            if field in ignore_fields:
                continue

            val1 = getattr(video1, field)
            val2 = getattr(video2, field)

            assert val1 == val2, f"Field '{field}' differs: {val1} != {val2}"


class ValidationIssueAssertions:
    """Assertions specific to ValidationIssue objects."""

    @staticmethod
    def assert_valid_validation_issue(issue: ValidationIssue):
        """Assert that a validation issue has valid properties."""
        assert issue.category, "Validation issue must have a category"
        assert issue.message, "Validation issue must have a message"
        assert issue.severity, "Validation issue must have a severity"

    @staticmethod
    def assert_issues_equal(
        issue1: ValidationIssue, issue2: ValidationIssue, ignore_fields: list[str] | None = None
    ):
        """Assert that two validation issues are equal."""
        if ignore_fields is None:
            ignore_fields = []

        for field in ["category", "message", "severity", "details"]:
            if field in ignore_fields:
                continue

            val1 = getattr(issue1, field)
            val2 = getattr(issue2, field)

            assert val1 == val2, f"Field '{field}' differs: {val1} != {val2}"


class MediaAssetsAssertions:
    """Assertions specific to MediaAssets objects."""

    @staticmethod
    def assert_valid_media_assets(assets: MediaAssets):
        """Assert that media assets are valid."""
        # All fields should be lists
        assert isinstance(assets.posters, list), "Posters must be a list"
        assert isinstance(assets.backgrounds, list), "Backgrounds must be a list"
        assert isinstance(assets.banners, list), "Banners must be a list"
        assert isinstance(assets.logos, list), "Logos must be a list"
        assert isinstance(assets.trailers, list), "Trailers must be a list"
        assert isinstance(assets.title_cards, list), "Title cards must be a list"
        assert isinstance(assets.subtitles, list), "Subtitles must be a list"
        assert isinstance(assets.nfo_files, list), "NFO files must be a list"

    @staticmethod
    def assert_has_assets(assets: MediaAssets, asset_types: list[str]):
        """Assert that specific asset types are present."""
        for asset_type in asset_types:
            asset_list = getattr(assets, asset_type, [])
            assert len(asset_list) > 0, f"No {asset_type} found in assets"


class PathAssertions:
    """Assertions for file paths and directories."""

    @staticmethod
    def assert_path_exists(path: Path | str):
        """Assert that a path exists."""
        path = Path(path) if isinstance(path, str) else path
        assert path.exists(), f"Path does not exist: {path}"

    @staticmethod
    def assert_file_created(path: Path | str, content: str | None = None):
        """Assert that a file was created with optional content check."""
        path = Path(path) if isinstance(path, str) else path
        assert path.exists(), f"File was not created: {path}"
        assert path.is_file(), f"Path is not a file: {path}"

        if content is not None:
            actual_content = path.read_text()
            assert content in actual_content, f"Expected content not found in file {path}"

    @staticmethod
    def assert_directory_structure(base_path: Path, expected_structure: dict[str, Any]):
        """Assert that a directory has the expected structure."""
        for name, value in expected_structure.items():
            path = base_path / name

            if isinstance(value, dict):
                assert path.is_dir(), f"Expected directory not found: {path}"
                PathAssertions.assert_directory_structure(path, value)
            else:
                assert path.exists(), f"Expected file not found: {path}"


class ValueAssertions:
    """General value assertions."""

    @staticmethod
    def assert_in_range(
        value: float | int,
        min_val: float | int | None = None,
        max_val: float | int | None = None,
        name: str = "Value",
    ):
        """Assert that a value is within a range."""
        if min_val is not None:
            assert value >= min_val, f"{name} ({value}) is below minimum ({min_val})"

        if max_val is not None:
            assert value <= max_val, f"{name} ({value}) is above maximum ({max_val})"

    @staticmethod
    def assert_close_to(
        actual: float, expected: float, tolerance: float = 0.01, name: str = "Value"
    ):
        """Assert that a float value is close to expected."""
        diff = abs(actual - expected)
        assert diff <= tolerance, (
            f"{name}: actual ({actual}) differs from expected ({expected}) "
            f"by {diff}, exceeding tolerance {tolerance}"
        )

    @staticmethod
    def assert_contains_all(container: list | set | dict, items: list, name: str = "Container"):
        """Assert that a container contains all specified items."""
        for item in items:
            assert item in container, f"{name} does not contain item: {item}"

    @staticmethod
    def assert_matches_pattern(text: str, pattern: str, name: str = "Text"):
        """Assert that text matches a regex pattern."""
        import re

        assert re.match(pattern, text), f"{name} '{text}' does not match pattern '{pattern}'"


def assert_async_result(coro, expected_result: Any = None, timeout: float = 5.0):
    """Assert that an async operation completes and optionally check result."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))

        if expected_result is not None:
            assert result == expected_result, (
                f"Async result {result} does not match expected {expected_result}"
            )

        return result
    except TimeoutError as err:
        raise AssertionError(f"Async operation timed out after {timeout} seconds") from err


def assert_no_exceptions(func: callable, *args, **kwargs):
    """Assert that a function call does not raise any exceptions."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        raise AssertionError(f"Function raised unexpected exception: {e}") from e
