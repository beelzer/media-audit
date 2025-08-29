"""Configuration module for the scanner."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ScannerConfig:
    """Scanner configuration with sensible defaults."""

    # Paths to scan
    root_paths: list[Path] = field(default_factory=list)

    # Patterns
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            "*.sample.*",
            "**/Extras/**",
            "**/Behind The Scenes/**",
            "**/Deleted Scenes/**",
            "**/.AppleDouble/**",
            "**/@eaDir/**",
        ]
    )

    # Media profiles
    profiles: list[str] = field(default_factory=lambda: ["plex", "jellyfin"])

    # Allowed codecs
    allowed_codecs: list[str] = field(default_factory=lambda: ["hevc", "h265", "av1"])

    # Performance
    concurrent_workers: int = 8
    cache_enabled: bool = True
    cache_dir: Path | None = None

    # Output
    output_path: Path = field(default_factory=lambda: Path("media-audit-report.html"))
    json_path: Path | None = None
    auto_open: bool = True
    problems_only: bool = False

    @classmethod
    def from_file(cls, path: Path) -> ScannerConfig:
        """Load configuration from YAML file."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScannerConfig:
        """Create config from dictionary."""
        config = cls()

        # Parse scan section
        if "scan" in data:
            scan = data["scan"]

            if "root_paths" in scan:
                config.root_paths = [Path(p) for p in scan["root_paths"]]

            if "profiles" in scan:
                config.profiles = scan["profiles"]

            if "allowed_codecs" in scan:
                config.allowed_codecs = scan["allowed_codecs"]

            if "include_patterns" in scan:
                config.include_patterns = scan["include_patterns"]

            if "exclude_patterns" in scan:
                config.exclude_patterns = scan["exclude_patterns"]

            if "concurrent_workers" in scan:
                config.concurrent_workers = scan["concurrent_workers"]

            if "cache_enabled" in scan:
                config.cache_enabled = scan["cache_enabled"]

            if "cache_dir" in scan:
                config.cache_dir = Path(scan["cache_dir"])

        # Parse report section
        if "report" in data:
            report = data["report"]

            if "output_path" in report:
                config.output_path = Path(report["output_path"])

            if "json_path" in report:
                config.json_path = Path(report["json_path"])

            if "auto_open" in report:
                config.auto_open = report["auto_open"]

            if "problems_only" in report:
                config.problems_only = report["problems_only"]

        return config

    def validate(self) -> list[str]:
        """Validate configuration and return any errors."""
        errors = []

        if not self.root_paths:
            errors.append("No root paths specified")

        for path in self.root_paths:
            if not path.exists():
                errors.append(f"Root path does not exist: {path}")

        if self.concurrent_workers < 1:
            errors.append("Concurrent workers must be at least 1")

        if self.concurrent_workers > 64:
            errors.append("Concurrent workers should not exceed 64")

        return errors
