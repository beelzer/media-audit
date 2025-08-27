"""Configuration management for media-audit."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .logging import get_logger
from .models import CodecType
from .patterns import MediaPatterns, get_patterns


@dataclass
class ScanConfig:
    """Configuration for media scanning."""

    root_paths: list[Path] = field(default_factory=list)
    profiles: list[str] = field(default_factory=lambda: ["all"])
    allowed_codecs: list[CodecType] = field(
        default_factory=lambda: [CodecType.HEVC, CodecType.H265, CodecType.AV1]
    )
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    patterns: MediaPatterns | None = None
    concurrent_workers: int = 4
    cache_enabled: bool = True
    cache_dir: Path | None = None

    def __post_init__(self) -> None:
        """Initialize patterns if not provided."""
        if self.patterns is None:
            self.patterns = get_patterns(self.profiles)

        # Convert string paths to Path objects
        self.root_paths = [Path(p) for p in self.root_paths]

        # Set default cache dir
        if self.cache_enabled and self.cache_dir is None:
            self.cache_dir = Path.home() / ".cache" / "media-audit"


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    output_path: Path | None = None
    json_path: Path | None = None
    auto_open: bool = False
    show_thumbnails: bool = True
    problems_only: bool = False


@dataclass
class Config:
    """Main configuration container."""

    scan: ScanConfig = field(default_factory=ScanConfig)
    report: ReportConfig = field(default_factory=ReportConfig)

    @classmethod
    def from_file(cls, path: Path) -> Config:
        """Load configuration from YAML file."""
        logger = get_logger("config")
        logger.info(f"Loading configuration from {path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            logger.debug(f"Successfully loaded config with keys: {list(data.keys())}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {path}: {e}")
            raise

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create configuration from dictionary."""
        scan_data = data.get("scan", {})
        report_data = data.get("report", {})

        # Handle codec conversion
        if "allowed_codecs" in scan_data:
            codecs = []
            for codec_str in scan_data["allowed_codecs"]:
                try:
                    codecs.append(CodecType[codec_str.upper()])
                except KeyError:
                    logger = get_logger("config")
                    logger.warning(f"Unknown codec type '{codec_str}', using OTHER")
                    codecs.append(CodecType.OTHER)
            scan_data["allowed_codecs"] = codecs

        # Handle custom patterns
        if "patterns" in scan_data:
            pattern_data = scan_data["patterns"]
            scan_data["patterns"] = MediaPatterns(**pattern_data)

        # Convert report paths to Path objects
        if "output_path" in report_data:
            report_data["output_path"] = Path(report_data["output_path"])
        if "json_path" in report_data:
            report_data["json_path"] = Path(report_data["json_path"])

        scan_config = ScanConfig(**scan_data)
        report_config = ReportConfig(**report_data)

        return cls(scan=scan_config, report=report_config)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        data = {
            "scan": {
                "root_paths": [str(p) for p in self.scan.root_paths],
                "profiles": self.scan.profiles,
                "allowed_codecs": [c.value for c in self.scan.allowed_codecs],
                "include_patterns": self.scan.include_patterns,
                "exclude_patterns": self.scan.exclude_patterns,
                "concurrent_workers": self.scan.concurrent_workers,
                "cache_enabled": self.scan.cache_enabled,
            },
            "report": {
                "auto_open": self.report.auto_open,
                "show_thumbnails": self.report.show_thumbnails,
                "problems_only": self.report.problems_only,
            },
        }

        if self.scan.cache_dir:
            data["scan"]["cache_dir"] = str(self.scan.cache_dir)  # type: ignore[index]

        if self.report.output_path:
            data["report"]["output_path"] = str(self.report.output_path)  # type: ignore[index]

        if self.report.json_path:
            data["report"]["json_path"] = str(self.report.json_path)  # type: ignore[index]

        return data

    def save(self, path: Path) -> None:
        """Save configuration to YAML file."""
        with open(path, "w") as f:
            yaml.safe_dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
