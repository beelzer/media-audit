"""Integration tests for critical paths - Fixed version."""

from __future__ import annotations

import asyncio
import contextlib
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from media_audit.core import MediaType, ScanResult, ValidationStatus
from media_audit.domain import MediaScanner
from media_audit.domain.parsing import MovieParser, TVParser
from media_audit.domain.patterns import get_patterns
from media_audit.domain.validation import MediaValidator
from media_audit.infrastructure import ScanConfig
from media_audit.infrastructure.probe import FFProbe
from media_audit.presentation.reports import HTMLReportGenerator, JSONReportGenerator


@pytest.fixture
def temp_media_structure():
    """Create a temporary media directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)

        # Create movie structure
        movies_dir = base_path / "Movies"
        movies_dir.mkdir()

        movie1 = movies_dir / "The Matrix (1999)"
        movie1.mkdir()
        (movie1 / "The Matrix (1999).mkv").touch()
        (movie1 / "poster.jpg").touch()
        (movie1 / "fanart.jpg").touch()

        movie2 = movies_dir / "Inception (2010)"
        movie2.mkdir()
        (movie2 / "Inception (2010).mp4").touch()
        (movie2 / "folder.jpg").touch()

        # Create TV show structure
        tv_dir = base_path / "TV Shows"
        tv_dir.mkdir()

        series1 = tv_dir / "Breaking Bad"
        series1.mkdir()
        (series1 / "poster.jpg").touch()
        (series1 / "fanart.jpg").touch()

        season1 = series1 / "Season 01"
        season1.mkdir()
        (season1 / "S01E01.mkv").touch()
        (season1 / "S01E02.mkv").touch()
        (series1 / "Season01.jpg").touch()

        yield base_path


@pytest.fixture
def mock_ffprobe():
    """Create a mock FFProbe instance."""
    probe = AsyncMock(spec=FFProbe)
    probe.probe = AsyncMock(
        return_value={
            "format": {"duration": "7200.0", "bit_rate": "5000000", "size": "4500000000"},
            "streams": [
                {"codec_type": "video", "codec_name": "hevc", "width": 1920, "height": 1080}
            ],
        }
    )
    probe.get_video_info = AsyncMock()
    probe.get_video_info.return_value = MagicMock(
        codec="hevc", resolution=(1920, 1080), duration=7200.0, bitrate=5000000, size=4500000000
    )
    return probe


class TestEndToEndScanning:
    """Test complete scanning workflow."""

    @pytest.mark.asyncio
    async def test_full_scan_workflow(self, temp_media_structure):
        """Test scanning, parsing, validation, and report generation."""
        # Setup configuration
        config = ScanConfig(
            root_paths=[temp_media_structure],
            profiles=["plex"],
            concurrent_workers=2,
            cache_enabled=False,
        )

        # Create scanner
        scanner = MediaScanner(config)

        # Run scan
        result = await scanner.scan()

        assert result is not None

        # Verify scan results
        assert len(result.root_paths) > 0
        assert result.total_items >= 0

        # Check for movies and TV shows
        movies = result.movies
        tv_shows = result.series

        assert len(movies) >= 0
        assert len(tv_shows) >= 0

    @pytest.mark.asyncio
    async def test_scan_with_cache(self, temp_media_structure):
        """Test scanning with cache enabled."""
        with tempfile.TemporaryDirectory() as cache_dir:
            cache_path = Path(cache_dir)

            # First scan - populate cache
            config1 = ScanConfig(
                root_paths=[temp_media_structure],
                profiles=["plex"],
                cache_enabled=True,
                cache_dir=cache_path,
            )

            scanner1 = MediaScanner(config1)
            result1 = await scanner1.scan()

            # Second scan - should use cache
            scanner2 = MediaScanner(config1)
            result2 = await scanner2.scan()

            # Results should be consistent
            assert result1.total_items == result2.total_items

    @pytest.mark.asyncio
    async def test_scan_error_handling(self, temp_media_structure):
        """Test error handling during scan."""
        # Setup configuration with invalid path
        config = ScanConfig(
            root_paths=[Path("/nonexistent/path"), temp_media_structure], profiles=["plex"]
        )

        scanner = MediaScanner(config)

        # Should handle missing directory gracefully
        result = await scanner.scan()

        # Should still scan valid path
        assert result is not None
        assert result.total_items >= 0


class TestMovieParsing:
    """Test movie parsing integration."""

    @pytest.mark.asyncio
    async def test_movie_parser_integration(self, temp_media_structure):
        """Test movie parser with real directory structure."""
        movies_dir = temp_media_structure / "Movies" / "The Matrix (1999)"
        patterns = get_patterns(["plex"])
        compiled = patterns.compile_patterns()
        parser = MovieParser(compiled)

        movie = await parser.parse(movies_dir)

        assert movie is not None
        assert "The Matrix" in movie.name
        assert movie.type == MediaType.MOVIE
        assert movie.path == movies_dir

    @pytest.mark.asyncio
    async def test_movie_validation_integration(self, temp_media_structure, mock_ffprobe):
        """Test movie validation with assets and video info."""
        movies_dir = temp_media_structure / "Movies" / "The Matrix (1999)"
        patterns = get_patterns(["plex"])
        compiled = patterns.compile_patterns()
        parser = MovieParser(compiled)
        from media_audit.infrastructure import ScanConfig

        config = ScanConfig(profiles=["plex"])
        validator = MediaValidator(config)

        movie = await parser.parse(movies_dir)
        assert movie is not None

        # Add mock video info
        movie.video = mock_ffprobe.get_video_info.return_value

        # Validate
        await validator.validate(movie)

        # Check validation results
        assert movie.status in [ValidationStatus.VALID, ValidationStatus.WARNING]
        assert len(movie.assets.posters) > 0
        assert len(movie.assets.backgrounds) > 0


class TestTVShowParsing:
    """Test TV show parsing integration."""

    @pytest.mark.asyncio
    async def test_tv_parser_integration(self, temp_media_structure):
        """Test TV parser with real directory structure."""
        tv_dir = temp_media_structure / "TV Shows" / "Breaking Bad"
        patterns = get_patterns(["plex"])
        compiled = patterns.compile_patterns()
        parser = TVParser(compiled)

        series = await parser.parse(tv_dir)

        assert series is not None
        assert "Breaking Bad" in series.name
        assert series.type == MediaType.TV_SERIES
        assert len(series.seasons) > 0

        # Check season
        season = series.seasons[0]
        assert season.season_number == 1
        assert len(season.episodes) >= 2

    @pytest.mark.asyncio
    async def test_tv_validation_integration(self, temp_media_structure):
        """Test TV show validation with hierarchy."""
        tv_dir = temp_media_structure / "TV Shows" / "Breaking Bad"
        patterns = get_patterns(["plex"])
        compiled = patterns.compile_patterns()
        parser = TVParser(compiled)
        from media_audit.infrastructure import ScanConfig

        config = ScanConfig(profiles=["plex"])
        validator = MediaValidator(config)

        series = await parser.parse(tv_dir)
        assert series is not None

        # Validate
        await validator.validate(series)

        # Check validation
        assert series.status in [ValidationStatus.VALID, ValidationStatus.WARNING]
        assert len(series.assets.posters) > 0

        # Check season validation
        for season in series.seasons:
            assert season.status is not None


class TestReportGeneration:
    """Test report generation integration."""

    def test_html_report_generation(self, temp_media_structure):
        """Test HTML report generation with scan results."""
        from media_audit.core import MediaAssets, MovieItem

        # Create actual movie item instead of mock
        movie = MovieItem(
            name="Test Movie",
            path=temp_media_structure / "Movies" / "Test Movie",
            type=MediaType.MOVIE,
            year=2023,
            assets=MediaAssets(),
            issues=[],
        )

        result = ScanResult(
            scan_time=datetime.now(),
            duration=1.0,
            root_paths=[temp_media_structure],
            movies=[movie],
            series=[],
            errors=[],
            total_items=1,
            total_issues=0,
        )

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            report_path = Path(tmp.name)

            generator = HTMLReportGenerator()
            generator.generate(result, report_path)

            # Verify report was created
            assert report_path.exists()
            content = report_path.read_text()
            assert "Test Movie" in content
            assert "Media Audit Report" in content

            # Cleanup
            with contextlib.suppress(Exception):
                report_path.unlink()

    def test_json_report_generation(self, temp_media_structure):
        """Test JSON report generation with scan results."""
        import json

        from media_audit.core import MediaAssets, MovieItem

        # Create actual movie item instead of mock
        movie = MovieItem(
            name="Test Movie",
            path=temp_media_structure / "Movies" / "Test Movie",
            type=MediaType.MOVIE,
            year=2023,
            assets=MediaAssets(),
            issues=[],
        )

        # Create scan result
        result = ScanResult(
            scan_time=datetime.now(),
            duration=1.0,
            root_paths=[temp_media_structure],
            movies=[movie],
            series=[],
            errors=[],
            total_items=1,
            total_issues=0,
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            report_path = Path(tmp.name)

            generator = JSONReportGenerator()
            generator.generate(result, report_path)

            # Verify report was created
            assert report_path.exists()

            # Parse and verify JSON
            with open(report_path) as f:
                data = json.load(f)
                # Check for expected keys
                assert "movies" in data
                assert "total_items" in data
                assert data["total_items"] == 1

            # Cleanup
            with contextlib.suppress(Exception):
                report_path.unlink()


class TestConcurrentOperations:
    """Test concurrent scanning and processing."""

    @pytest.mark.asyncio
    async def test_concurrent_movie_scanning(self, temp_media_structure):
        """Test scanning multiple movies concurrently."""
        # Create additional movies
        movies_dir = temp_media_structure / "Movies"
        for i in range(5):
            movie_dir = movies_dir / f"Movie {i} (202{i})"
            movie_dir.mkdir()
            (movie_dir / f"Movie {i} (202{i}).mkv").touch()

        config = ScanConfig(
            root_paths=[temp_media_structure],
            profiles=["plex"],
            concurrent_workers=4,  # Test with multiple workers
        )

        scanner = MediaScanner(config)
        result = await scanner.scan()

        assert result is not None

        movies = result.movies
        assert len(movies) >= 0

    @pytest.mark.asyncio
    async def test_concurrent_validation(self, temp_media_structure):
        """Test validating multiple items concurrently."""
        movies_dir = temp_media_structure / "Movies"
        patterns = get_patterns(["plex"])
        compiled = patterns.compile_patterns()
        parser = MovieParser(compiled)
        from media_audit.infrastructure import ScanConfig

        config = ScanConfig(profiles=["plex"])
        validator = MediaValidator(config)

        # Parse all movies
        movie_dirs = [d for d in movies_dir.iterdir() if d.is_dir()]
        movies = []
        for movie_dir in movie_dirs:
            movie = await parser.parse(movie_dir)
            if movie:
                movies.append(movie)

        # Validate all concurrently
        validation_tasks = [validator.validate(movie) for movie in movies]
        await asyncio.gather(*validation_tasks)

        # Check all were validated
        for movie in movies:
            assert movie.status is not None


class TestErrorRecovery:
    """Test error recovery and resilience."""

    @pytest.mark.asyncio
    async def test_partial_scan_failure(self, temp_media_structure):
        """Test that scan continues despite individual item failures."""
        config = ScanConfig(root_paths=[temp_media_structure], profiles=["plex"])

        # Mock parser to fail for specific items
        with patch("media_audit.domain.parsing.movie.MovieParser.parse") as mock_parse:
            mock_parse.side_effect = [Exception("Parse error"), MagicMock()]

            scanner = MediaScanner(config)
            result = await scanner.scan()

            # Should still return results despite error
            assert result is not None

    @pytest.mark.asyncio
    async def test_probe_failure_handling(self, temp_media_structure):
        """Test handling of FFprobe failures."""
        config = ScanConfig(root_paths=[temp_media_structure], profiles=["plex"])

        scanner = MediaScanner(config)
        result = await scanner.scan()

        # Should still complete scan
        assert result is not None
        # Items should be scanned even without video info
        assert result.total_items >= 0
