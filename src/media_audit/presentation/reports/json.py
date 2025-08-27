"""JSON report generator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from media_audit.core import (
    EpisodeItem,
    MediaAssets,
    MovieItem,
    ScanResult,
    SeasonItem,
    SeriesItem,
    ValidationIssue,
    VideoInfo,
)
from media_audit.shared import get_logger


class JSONReportGenerator:
    """Generates JSON reports from scan results."""

    def __init__(self) -> None:
        """Initialize JSON report generator."""
        self.logger = get_logger("report.json")

    def generate(self, result: ScanResult, output_path: Path) -> None:
        """Generate JSON report file."""
        self.logger.info(f"Generating JSON report: {output_path}")
        data = self._serialize_result(result)

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.debug(f"Successfully wrote JSON report to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to write JSON report: {e}")
            raise

    def _serialize_result(self, result: ScanResult) -> dict[str, Any]:
        """Serialize scan result to dictionary."""
        return {
            "scan_time": result.scan_time.isoformat() if result.scan_time else None,
            "duration": result.duration,
            "root_paths": [str(p) for p in result.root_paths],
            "total_items": result.total_items,
            "total_issues": result.total_issues,
            "errors": result.errors,
            "movies": [self._serialize_movie(m) for m in result.movies],
            "series": [self._serialize_series(s) for s in result.series],
        }

    def _serialize_movie(self, movie: MovieItem) -> dict[str, Any]:
        """Serialize movie item."""
        return {
            "path": str(movie.path),
            "name": movie.name,
            "year": movie.year,
            "imdb_id": movie.imdb_id,
            "tmdb_id": movie.tmdb_id,
            "release_group": movie.release_group,
            "quality": movie.quality,
            "source": movie.source,
            "status": movie.status.value,
            "issues": self._serialize_issues(movie.issues),
            "assets": self._serialize_assets(movie.assets),
            "video_info": self._serialize_video_info(movie.video_info)
            if movie.video_info
            else None,
        }

    def _serialize_series(self, series: SeriesItem) -> dict[str, Any]:
        """Serialize series item."""
        return {
            "path": str(series.path),
            "name": series.name,
            "imdb_id": series.imdb_id,
            "tvdb_id": series.tvdb_id,
            "tmdb_id": series.tmdb_id,
            "status": series.status.value,
            "total_episodes": series.total_episodes,
            "issues": self._serialize_issues(series.issues),
            "assets": self._serialize_assets(series.assets),
            "seasons": [self._serialize_season(s) for s in series.seasons],
        }

    def _serialize_season(self, season: SeasonItem) -> dict[str, Any]:
        """Serialize season item."""
        return {
            "path": str(season.path),
            "name": season.name,
            "season_number": season.season_number,
            "status": season.status.value,
            "issues": self._serialize_issues(season.issues),
            "assets": self._serialize_assets(season.assets),
            "episodes": [self._serialize_episode(e) for e in season.episodes],
        }

    def _serialize_episode(self, episode: EpisodeItem) -> dict[str, Any]:
        """Serialize episode item."""
        return {
            "path": str(episode.path),
            "name": episode.name,
            "season_number": episode.season_number,
            "episode_number": episode.episode_number,
            "title": episode.title,  # Fixed: EpisodeItem uses 'title' not 'episode_title'
            "status": episode.status.value,
            "issues": self._serialize_issues(episode.issues),
            "assets": self._serialize_assets(episode.assets),
            "metadata": episode.metadata,  # Include metadata dict which has quality, source, etc.
            "video_info": self._serialize_video_info(episode.video_info)
            if episode.video_info
            else None,
        }

    def _serialize_issues(self, issues: list[ValidationIssue]) -> list[dict[str, Any]]:
        """Serialize validation issues."""
        return [
            {
                "category": issue.category,
                "message": issue.message,
                "severity": issue.severity.value,
                "details": issue.details,
            }
            for issue in issues
        ]

    def _serialize_assets(self, assets: MediaAssets) -> dict[str, list[str]]:
        """Serialize media assets."""
        return {
            "posters": [str(p) for p in assets.posters],
            "backgrounds": [str(p) for p in assets.backgrounds],
            "banners": [str(p) for p in assets.banners],
            "trailers": [str(p) for p in assets.trailers],
            "title_cards": [str(p) for p in assets.title_cards],
        }

    def _serialize_video_info(self, video_info: VideoInfo) -> dict[str, Any]:
        """Serialize video information."""
        return {
            "path": str(video_info.path),
            "codec": video_info.codec.value if video_info.codec else None,
            "resolution": video_info.resolution,
            "duration": video_info.duration,
            "bitrate": video_info.bitrate,
            "size": video_info.size,
        }
