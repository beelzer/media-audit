"""TV show parser implementation."""

from __future__ import annotations

import asyncio
import contextlib
import re
from pathlib import Path
from typing import Any

import aiofiles

from media_audit.core import (
    EpisodeItem,
    MediaAssets,
    MediaType,
    SeasonItem,
    SeriesItem,
    VideoInfo,
)
from media_audit.shared.logging import get_logger

from .base import BaseParser


class TVParser(BaseParser):
    """Parser for TV show content."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize TV parser."""
        super().__init__(*args, **kwargs)
        self.logger = get_logger("parser.tv")

    async def parse(self, directory: Path) -> SeriesItem | None:
        """Parse a TV series directory."""
        if not directory.is_dir():
            self.logger.debug(f"Skipping non-directory: {directory}")
            return None

        self.logger.debug(f"Parsing TV series: {directory.name}")
        series_name = directory.name

        # Create series item
        series = SeriesItem(
            path=directory,
            name=series_name,
            type=MediaType.TV_SERIES,
        )

        # Check for .plexmatch file with metadata
        plexmatch_file = directory / ".plexmatch"
        if plexmatch_file.exists():
            await self._parse_plexmatch(plexmatch_file, series)

        # Scan for series-level assets
        series.assets = self.scan_series_assets(directory)

        # Find and parse seasons
        season_dirs = self.find_season_directories(directory)

        # Parse seasons concurrently
        season_tasks = [
            self.parse_season(season_dir, series.path) for season_dir in sorted(season_dirs)
        ]
        seasons = await asyncio.gather(*season_tasks)

        for season in seasons:
            if season:
                series.seasons.append(season)

        # Also check for episodes directly in series folder (single season shows)
        root_episodes = self.find_episodes(directory)
        if root_episodes and not series.seasons:
            # Create implicit Season 1
            season = SeasonItem(
                path=directory,
                name="Season 1",
                season_number=1,
                type=MediaType.TV_SEASON,
            )
            for ep_path, ep_info in root_episodes:
                episode = self.create_episode(ep_path, ep_info)
                if episode:
                    season.episodes.append(episode)

            if season.episodes:
                series.seasons.append(season)

        # Episode count is calculated automatically via property
        return series

    async def parse_season(self, directory: Path, series_path: Path) -> SeasonItem | None:
        """Parse a season directory."""
        season_number = self.extract_season_number(directory.name)
        if season_number is None:
            return None

        season = SeasonItem(
            path=directory,
            name=directory.name,
            season_number=season_number,
            type=MediaType.TV_SEASON,
        )

        # Scan for season-level assets
        season.assets = self.scan_season_assets(directory, season_number)

        # Find episodes
        episodes = self.find_episodes(directory)
        for ep_path, ep_info in episodes:
            episode = self.create_episode(ep_path, ep_info)
            if episode:
                season.episodes.append(episode)

        # Sort episodes by episode number
        season.episodes.sort(key=lambda e: (e.season_number, e.episode_number))

        return season

    def create_episode(self, video_path: Path, ep_info: dict[str, Any]) -> EpisodeItem | None:
        """Create an episode item from video file."""
        episode = EpisodeItem(
            path=video_path.parent,
            name=video_path.stem,
            type=MediaType.TV_EPISODE,
            season_number=ep_info["season"],
            episode_number=ep_info["episode"],
            title=ep_info.get("title"),
            video_info=VideoInfo(path=video_path),
        )

        # Extract metadata from filename
        video_name = video_path.stem
        # Store metadata in the metadata dict instead of direct attributes
        episode.metadata["source"] = self.extract_source(video_name)
        episode.metadata["release_group"] = self.extract_release_group(video_name)
        episode.metadata["quality"] = self.extract_quality(video_name)

        # Look for episode title card
        episode.assets = self.scan_episode_assets(video_path)

        return episode

    def find_season_directories(self, directory: Path) -> list[Path]:
        """Find season directories in series folder."""
        season_dirs = []

        for item in directory.iterdir():
            if item.is_dir() and self.extract_season_number(item.name) is not None:
                season_dirs.append(item)

        return season_dirs

    def find_episodes(self, directory: Path) -> list[tuple[Path, dict[str, Any]]]:
        """Find episode files in directory."""
        episodes = []

        for file_path in directory.iterdir():
            if file_path.is_file() and self.is_video_file(file_path):
                ep_info = self.parse_episode_info(file_path.name)
                if ep_info:
                    episodes.append((file_path, ep_info))

        return sorted(episodes, key=lambda x: (x[1]["season"], x[1]["episode"]))

    def parse_episode_info(self, filename: str) -> dict[str, Any] | None:
        """Extract episode information from filename."""
        # Common patterns: S01E01, 1x01, etc.
        patterns = [
            r"S(\d+)E(\d+)",  # S01E01
            r"(\d+)x(\d+)",  # 1x01
            r"Season\s*(\d+)\s*Episode\s*(\d+)",  # Season 1 Episode 1
        ]

        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return {
                    "season": int(match.group(1)),
                    "episode": int(match.group(2)),
                    "title": self.extract_episode_title(filename),
                }

        return None

    def extract_episode_title(self, filename: str) -> str | None:
        """Extract episode title from filename."""
        # Remove episode numbering and extension
        title = re.sub(r"S\d+E\d+", "", filename, flags=re.IGNORECASE)
        title = re.sub(r"\d+x\d+", "", title)
        title = re.sub(r"Season\s*\d+\s*Episode\s*\d+", "", title, flags=re.IGNORECASE)

        # Remove common separators and clean up
        title = re.sub(r"[\._-]+", " ", title)
        title = re.sub(r"\[.*?\]", "", title)  # Remove brackets
        title = re.sub(r"\(.*?\)", "", title)  # Remove parentheses
        title = title.strip()

        return title if title else None

    def extract_season_number(self, name: str) -> int | None:
        """Extract season number from directory name."""
        patterns = [
            r"Season\s*(\d+)",
            r"S(\d+)",
            r"Series\s*(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def scan_series_assets(self, directory: Path) -> MediaAssets:
        """Scan for series-level assets."""
        assets = MediaAssets()

        for item in directory.iterdir():
            if item.is_file():
                classification = self.classify_asset(item, directory)
                if classification:
                    asset_type, path = classification
                    # Only collect series-level assets (not season-specific)
                    if not re.search(r"Season\s*\d+", item.name, re.IGNORECASE):
                        if asset_type == "poster":
                            assets.posters.append(path)
                        elif asset_type == "background":
                            assets.backgrounds.append(path)
                        elif asset_type == "banner":
                            assets.banners.append(path)

        return assets

    def scan_season_assets(self, directory: Path, season_number: int) -> MediaAssets:
        """Scan for season-level assets."""
        assets = MediaAssets()

        # Look for season poster
        season_patterns = [
            f"Season{season_number:02d}",
            f"Season{season_number}",
            f"S{season_number:02d}",
        ]

        parent = directory.parent
        for pattern in season_patterns:
            for ext in self.IMAGE_EXTENSIONS:
                poster_path = parent / f"{pattern}{ext}"
                if poster_path.exists():
                    assets.posters.append(poster_path)

                banner_path = parent / f"{pattern}-banner{ext}"
                if banner_path.exists():
                    assets.banners.append(banner_path)

        return assets

    def scan_episode_assets(self, video_path: Path) -> MediaAssets:
        """Scan for episode-specific assets."""
        assets = MediaAssets()

        # Look for title card with same base name
        base_name = video_path.stem

        for ext in self.IMAGE_EXTENSIONS:
            title_card_path = video_path.parent / f"{base_name}{ext}"
            if title_card_path.exists():
                assets.title_cards.append(title_card_path)

            # Also check for -thumb variant
            thumb_path = video_path.parent / f"{base_name}-thumb{ext}"
            if thumb_path.exists():
                assets.title_cards.append(thumb_path)

        return assets

    def is_tv_directory(self, directory: Path) -> bool:
        """Check if directory appears to be a TV series."""
        if not directory.is_dir():
            return False

        # Check for season folders - this is the primary indicator
        has_season_folders = any(
            self.extract_season_number(d.name) is not None
            for d in directory.iterdir()
            if d.is_dir()
        )

        return has_season_folders

    async def _parse_plexmatch(self, plexmatch_file: Path, series: SeriesItem) -> None:
        """Parse .plexmatch file for metadata."""
        try:
            async with aiofiles.open(plexmatch_file, encoding="utf-8") as f:
                content = await f.read()
                for line in content.split("\n"):
                    line = line.strip()
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()

                        if key == "title":
                            series.name = value
                        elif key == "year":
                            with contextlib.suppress(ValueError):
                                series.year_started = int(value)
                        elif key in {"imdbid", "imdb_id"}:
                            series.imdb_id = value
                        elif key in {"tvdbid", "tvdb_id"}:
                            series.tvdb_id = value
        except Exception as e:
            self.logger.debug(f"Failed to parse plexmatch file: {e}")
