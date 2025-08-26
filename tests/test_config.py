"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest
import yaml

from media_audit.config import Config, ScanConfig, ReportConfig
from media_audit.models import CodecType


def test_scan_config_defaults():
    """Test ScanConfig default values."""
    config = ScanConfig()
    
    assert config.root_paths == []
    assert config.profiles == ["all"]
    assert CodecType.HEVC in config.allowed_codecs
    assert CodecType.AV1 in config.allowed_codecs
    assert config.concurrent_workers == 4
    assert config.cache_enabled is True


def test_report_config_defaults():
    """Test ReportConfig default values."""
    config = ReportConfig()
    
    assert config.output_path is None
    assert config.json_path is None
    assert config.auto_open is False
    assert config.show_thumbnails is True
    assert config.problems_only is False


def test_config_from_dict():
    """Test creating config from dictionary."""
    data = {
        "scan": {
            "root_paths": ["/media/Movies", "/media/TV"],
            "profiles": ["plex"],
            "allowed_codecs": ["hevc", "av1"],
            "concurrent_workers": 8,
        },
        "report": {
            "output_path": "report.html",
            "auto_open": True,
        },
    }
    
    config = Config.from_dict(data)
    
    assert len(config.scan.root_paths) == 2
    assert config.scan.profiles == ["plex"]
    assert len(config.scan.allowed_codecs) == 2
    assert config.scan.concurrent_workers == 8
    assert config.report.auto_open is True


def test_config_save_load():
    """Test saving and loading config from YAML."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Create and save config
        config = Config(
            scan=ScanConfig(
                root_paths=[Path("/media")],
                profiles=["jellyfin"],
            ),
            report=ReportConfig(
                output_path=Path("output.html"),
                auto_open=True,
            ),
        )
        
        config.save(temp_path)
        
        # Load and verify
        loaded_config = Config.from_file(temp_path)
        
        assert len(loaded_config.scan.root_paths) == 1
        assert loaded_config.scan.profiles == ["jellyfin"]
        assert loaded_config.report.auto_open is True
        
    finally:
        temp_path.unlink()


def test_config_codec_conversion():
    """Test codec string to enum conversion."""
    data = {
        "scan": {
            "allowed_codecs": ["hevc", "H264", "AV1", "invalid"],
        }
    }
    
    config = Config.from_dict(data)
    
    assert CodecType.HEVC in config.scan.allowed_codecs
    assert CodecType.H264 in config.scan.allowed_codecs
    assert CodecType.AV1 in config.scan.allowed_codecs
    assert CodecType.OTHER in config.scan.allowed_codecs  # Invalid becomes OTHER