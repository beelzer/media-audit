"""Tests for metadata extraction functionality."""

from __future__ import annotations

import pytest

from media_audit.domain.parsing import MovieParser, TVParser
from media_audit.domain.patterns import get_patterns


@pytest.fixture
def movie_parser():
    """Create a movie parser instance."""
    patterns = get_patterns(["all"]).compile_patterns()
    return MovieParser(patterns)


@pytest.fixture
def tv_parser():
    """Create a TV parser instance."""
    patterns = get_patterns(["all"]).compile_patterns()
    return TVParser(patterns)


def test_extract_imdb_id(movie_parser):
    """Test IMDB ID extraction."""
    assert movie_parser.extract_imdb_id("Jason X (2001) {imdb-tt0211443}") == "tt0211443"
    assert movie_parser.extract_imdb_id("Movie (2023) tt1234567") == "tt1234567"
    assert movie_parser.extract_imdb_id("No IMDB ID") is None


def test_extract_release_group(movie_parser):
    """Test release group extraction."""
    assert movie_parser.extract_release_group("Movie.2023.1080p-RARBG.mkv") == "RARBG"
    assert movie_parser.extract_release_group("Movie [successfulcrab].mkv") == "successfulcrab"
    assert movie_parser.extract_release_group("Movie-NTb.mp4") == "NTb"
    assert movie_parser.extract_release_group("No Group.mkv") is None


def test_extract_quality(movie_parser):
    """Test quality extraction."""
    assert movie_parser.extract_quality("Movie.1080p.BluRay.mkv") == "1080p"
    assert movie_parser.extract_quality("Movie.2160p.4K.mkv") == "2160p"
    assert movie_parser.extract_quality("Movie.720p.mkv") == "720p"
    assert movie_parser.extract_quality("Movie.4K.UHD.mkv") == "4K"
    assert movie_parser.extract_quality("No quality.mkv") is None


def test_extract_source(movie_parser):
    """Test source extraction."""
    assert movie_parser.extract_source("Movie.BluRay.1080p.mkv") == "BluRay"
    assert movie_parser.extract_source("Movie.WEB-DL.mkv") == "WEBDL"
    assert movie_parser.extract_source("Movie.WEBDL.mkv") == "WEBDL"
    assert movie_parser.extract_source("Movie.WEBRip.mkv") == "WEBRip"
    assert movie_parser.extract_source("Movie.HDTV.mkv") == "HDTV"
    assert movie_parser.extract_source("Movie.BRRip.mkv") == "BRRip"
    assert movie_parser.extract_source("No source.mkv") is None


@pytest.mark.asyncio
async def test_movie_metadata_parsing(movie_parser, tmp_path):
    """Test complete movie metadata extraction."""
    # Create movie directory with metadata in name
    movie_dir = tmp_path / "Jason X (2001) {imdb-tt0211443}"
    movie_dir.mkdir()

    # Create video file with quality info
    video_file = movie_dir / "Jason.X.2001.Bluray-1080p.AAC.5.1.x264-RARBG.mkv"
    video_file.write_text("")

    # Parse movie
    movie = await movie_parser.parse(movie_dir)

    assert movie is not None
    assert movie.name == "Jason X"
    assert movie.year == 2001
    assert movie.imdb_id == "tt0211443"
    assert movie.quality == "1080p"
    assert movie.source == "BluRay"
    assert movie.release_group == "RARBG"


@pytest.mark.asyncio
async def test_episode_metadata_parsing(tv_parser, tmp_path):
    """Test episode metadata extraction."""
    # Create series directory
    series_dir = tmp_path / "Peacemaker (2022)"
    series_dir.mkdir()

    # Create season directory
    season_dir = series_dir / "Season 2"
    season_dir.mkdir()

    # Create episode with metadata
    episode_file = (
        season_dir
        / "Peacemaker.S02E01.The.Ties.That.Grind.WEBDL-1080p.EAC3.5.1.h264-successfulcrab.mkv"
    )
    episode_file.write_text("")

    # Parse series
    series = await tv_parser.parse(series_dir)

    assert series is not None
    assert len(series.seasons) == 1
    assert len(series.seasons[0].episodes) == 1

    episode = series.seasons[0].episodes[0]
    assert episode.season_number == 2
    assert episode.episode_number == 1
    assert episode.metadata["quality"] == "1080p"
    assert episode.metadata["source"] == "WEBDL"
    assert episode.metadata["release_group"] == "successfulcrab"


@pytest.mark.asyncio
async def test_plexmatch_parsing(tv_parser, tmp_path):
    """Test .plexmatch file parsing."""
    # Create series directory
    series_dir = tmp_path / "Test Series"
    series_dir.mkdir()

    # Create .plexmatch file
    plexmatch_file = series_dir / ".plexmatch"
    plexmatch_file.write_text("""TvdbId: 391153
ImdbId: tt13146488
TmdbId: 110492
""")

    # Create a season so it's recognized as TV
    (series_dir / "Season 1").mkdir()

    # Parse series
    series = await tv_parser.parse(series_dir)

    assert series is not None
    assert series.tvdb_id == "391153"
    assert series.imdb_id == "tt13146488"
    assert series.tmdb_id == "110492"
