"""JSON report generator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models import ScanResult, MediaItem, VideoInfo


class JSONReportGenerator:
    """Generates JSON reports from scan results."""

    def generate(self, result: ScanResult, output_path: Path) -> None:
        """Generate JSON report file."""
        data = self._serialize_result(result)
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _serialize_result(self, result: ScanResult) -> dict[str, Any]:
        """Serialize scan result to dictionary."""
        return {
            "scan_time": result.scan_time.isoformat(),
            "duration": result.duration,
            "root_paths": [str(p) for p in result.root_paths],
            "total_items": result.total_items,
            "total_issues": result.total_issues,
            "errors": result.errors,
            "movies": [self._serialize_movie(m) for m in result.movies],
            "series": [self._serialize_series(s) for s in result.series],
        }

    def _serialize_movie(self, movie) -> dict[str, Any]:
        """Serialize movie item."""
        return {
            "path": str(movie.path),
            "name": movie.name,
            "year": movie.year,
            "status": movie.status.value,
            "issues": self._serialize_issues(movie.issues),
            "assets": self._serialize_assets(movie.assets),
            "video_info": self._serialize_video_info(movie.video_info) if movie.video_info else None,
        }

    def _serialize_series(self, series) -> dict[str, Any]:
        """Serialize series item."""
        return {
            "path": str(series.path),
            "name": series.name,
            "status": series.status.value,
            "total_episodes": series.total_episodes,
            "issues": self._serialize_issues(series.issues),
            "assets": self._serialize_assets(series.assets),
            "seasons": [self._serialize_season(s) for s in series.seasons],
        }

    def _serialize_season(self, season) -> dict[str, Any]:
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

    def _serialize_episode(self, episode) -> dict[str, Any]:
        """Serialize episode item."""
        return {
            "path": str(episode.path),
            "name": episode.name,
            "season_number": episode.season_number,
            "episode_number": episode.episode_number,
            "episode_title": episode.episode_title,
            "status": episode.status.value,
            "issues": self._serialize_issues(episode.issues),
            "assets": self._serialize_assets(episode.assets),
            "video_info": self._serialize_video_info(episode.video_info) if episode.video_info else None,
        }

    def _serialize_issues(self, issues) -> list[dict[str, Any]]:
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

    def _serialize_assets(self, assets) -> dict[str, list[str]]:
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