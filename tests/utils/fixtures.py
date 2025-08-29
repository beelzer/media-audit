"""
Reusable test fixtures and test data management.
"""

import json
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import yaml


class TestDataManager:
    """Manage test data files and fixtures."""

    def __init__(self, base_path: Path | None = None):
        self.base_path = base_path or Path(__file__).parent.parent / "fixtures"
        self.base_path.mkdir(exist_ok=True, parents=True)

    def load_json(self, filename: str) -> dict[str, Any]:
        """Load JSON test data."""
        path = self.base_path / filename
        if not path.suffix:
            path = path.with_suffix(".json")

        with open(path) as f:
            return json.load(f)

    def load_yaml(self, filename: str) -> dict[str, Any]:
        """Load YAML test data."""
        path = self.base_path / filename
        if not path.suffix:
            path = path.with_suffix(".yaml")

        with open(path) as f:
            return yaml.safe_load(f)

    def save_snapshot(self, name: str, data: Any) -> Path:
        """Save test snapshot for comparison."""
        snapshot_dir = self.base_path / "snapshots"
        snapshot_dir.mkdir(exist_ok=True)

        path = snapshot_dir / f"{name}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return path

    def compare_snapshot(self, name: str, data: Any) -> bool:
        """Compare data against saved snapshot."""
        path = self.base_path / "snapshots" / f"{name}.json"

        if not path.exists():
            self.save_snapshot(name, data)
            return True

        with open(path) as f:
            expected = json.load(f)

        return expected == data


class MediaFileBuilder:
    """Builder for creating realistic media file structures."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.structure = {}

    def add_movie(
        self, title: str, year: int = 2024, with_assets: bool = False, with_subtitles: bool = False
    ) -> "MediaFileBuilder":
        """Add a movie with optional assets."""
        movie_dir = self.base_path / f"{title}.{year}"
        movie_dir.mkdir(exist_ok=True, parents=True)

        # Create main video file
        video_file = movie_dir / f"{title}.{year}.1080p.mkv"
        video_file.touch()

        if with_assets:
            (movie_dir / "poster.jpg").touch()
            (movie_dir / "fanart.jpg").touch()
            (movie_dir / "movie.nfo").touch()

        if with_subtitles:
            (movie_dir / f"{title}.{year}.en.srt").touch()
            (movie_dir / f"{title}.{year}.fr.srt").touch()

        self.structure[title] = movie_dir
        return self

    def add_tv_show(
        self,
        series: str,
        seasons: int = 1,
        episodes_per_season: int = 10,
        with_assets: bool = False,
    ) -> "MediaFileBuilder":
        """Add a TV show with seasons and episodes."""
        show_dir = self.base_path / series
        show_dir.mkdir(exist_ok=True, parents=True)

        if with_assets:
            (show_dir / "poster.jpg").touch()
            (show_dir / "fanart.jpg").touch()
            (show_dir / "tvshow.nfo").touch()

        for season in range(1, seasons + 1):
            season_dir = show_dir / f"Season {season:02d}"
            season_dir.mkdir(exist_ok=True)

            if with_assets:
                (season_dir / f"season{season:02d}-poster.jpg").touch()

            for episode in range(1, episodes_per_season + 1):
                ep_file = season_dir / f"{series}.S{season:02d}E{episode:02d}.mkv"
                ep_file.touch()

        self.structure[series] = show_dir
        return self

    def build(self) -> dict[str, Path]:
        """Return the created structure."""
        return self.structure


@contextmanager
def temp_media_library(movies: int = 0, tv_shows: int = 0, with_assets: bool = False):
    """Create a temporary media library for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        builder = MediaFileBuilder(temp_path)

        # Add movies
        for i in range(movies):
            builder.add_movie(f"Test_Movie_{i + 1}", 2020 + i, with_assets=with_assets)

        # Add TV shows
        for i in range(tv_shows):
            builder.add_tv_show(
                f"Test_Show_{i + 1}", seasons=2, episodes_per_season=5, with_assets=with_assets
            )

        yield builder.build()


class PerformanceTimer:
    """Context manager for performance testing."""

    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.elapsed = None

    def __enter__(self):
        import time

        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        import time

        self.end_time = time.perf_counter()
        self.elapsed = self.end_time - self.start_time

    def assert_under(self, seconds: float):
        """Assert operation completed under time limit."""
        if self.elapsed is None:
            raise RuntimeError("Timer not used in context manager")

        assert self.elapsed < seconds, (
            f"{self.name} took {self.elapsed:.3f}s, expected under {seconds}s"
        )


class TestDataSet:
    """Predefined test datasets for common scenarios."""

    @staticmethod
    def edge_cases() -> list[dict[str, Any]]:
        """Get edge case test data."""
        return [
            {"name": "empty_string", "value": ""},
            {"name": "very_long_string", "value": "x" * 10000},
            {"name": "special_chars", "value": "!@#$%^&*()[]{}|\\<>?,./"},
            {"name": "unicode", "value": "🎬 電影 фильм 映画"},
            {"name": "null_bytes", "value": "test\x00value"},
            {"name": "path_traversal", "value": "../../../etc/passwd"},
            {"name": "max_int", "value": 2**31 - 1},
            {"name": "negative", "value": -1},
            {"name": "float_precision", "value": 0.1 + 0.2},
        ]

    @staticmethod
    def media_filenames() -> list[str]:
        """Get realistic media filename test data."""
        return [
            # Movies
            "The.Matrix.1999.1080p.BluRay.x264.mkv",
            "Inception.2010.2160p.UHD.BluRay.x265.HDR.mkv",
            "Parasite.2019.KOREAN.1080p.WEB-DL.H264.mkv",
            "The Lord of the Rings - The Fellowship of the Ring (2001) Extended.mkv",
            # TV Shows
            "Breaking.Bad.S01E01.Pilot.1080p.BluRay.mkv",
            "Game.of.Thrones.S08E06.REPACK.1080p.WEB.H264.mkv",
            "The.Office.US.S09E23.Finale.Part.2.mkv",
            "Stranger Things - 4x09 - The Piggyback.mkv",
            # Edge cases
            "movie.mkv",
            "MOVIE.MKV",
            "movie with spaces.mkv",
            "movie.with.many.dots.2024.mkv",
            "2024.mkv",
            "S01E01.mkv",
        ]

    @staticmethod
    def invalid_media_files() -> list[str]:
        """Get invalid media filename test data."""
        return [
            "document.pdf",
            "image.jpg",
            "README.md",
            ".hidden.mkv",
            "movie.txt",
            "",
            ".",
            "..",
            "CON.mkv",  # Windows reserved name
            "movie?.mkv",  # Invalid character
            "movie*.mkv",  # Invalid character
        ]


def parametrize_with_ids(test_data: list[Any], id_func=str):
    """Helper to create parametrize decorator with meaningful IDs."""
    import pytest

    ids = [id_func(data) if callable(id_func) else str(data) for data in test_data]
    return pytest.mark.parametrize("test_input", test_data, ids=ids)
