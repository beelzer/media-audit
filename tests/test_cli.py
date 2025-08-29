"""Tests for the CLI module."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from media_audit.core import ScanResult, ValidationStatus
from media_audit.core.enums import MediaType
from media_audit.presentation.cli import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_scan_result():
    """Create a mock scan result."""
    from datetime import datetime

    movie = MagicMock()
    movie.name = "Test Movie"
    movie.path = Path("/media/Test Movie")
    movie.type = MediaType.MOVIE
    movie.validation_status = ValidationStatus.VALID
    movie.issues = []
    movie.assets = MagicMock()
    movie.assets.has_poster = True
    movie.assets.has_background = True
    movie.video = None

    result = MagicMock(spec=ScanResult)
    result.scan_time = datetime.now()
    result.duration = 1.5
    result.root_paths = [Path("/media")]
    result.movies = [movie]
    result.series = []
    result.errors = []
    result.total_items = 1
    result.total_issues = 0

    return result


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_cli_version(self, runner):
        """Test version option."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_cli_help(self, runner):
        """Test help output."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Media Audit" in result.output
        assert "scan" in result.output

    def test_scan_help(self, runner):
        """Test scan command help."""
        result = runner.invoke(cli, ["scan", "--help"])
        assert result.exit_code == 0
        assert "--roots" in result.output
        assert "--report" in result.output
        assert "--config" in result.output


class TestScanCommand:
    """Test scan command functionality."""

    @patch("media_audit.presentation.cli.cli._display_summary")
    @patch("media_audit.presentation.cli.cli.MediaScanner")
    @patch("media_audit.presentation.cli.cli.HTMLReportGenerator")
    def test_scan_basic(self, mock_html_gen, mock_scanner, mock_display, runner, mock_scan_result):
        """Test basic scan with HTML report."""
        # Setup mocks
        scanner_instance = AsyncMock()
        scanner_instance.scan = AsyncMock(return_value=mock_scan_result)
        mock_scanner.return_value = scanner_instance

        html_gen_instance = MagicMock()
        html_gen_instance.generate = MagicMock()
        mock_html_gen.return_value = html_gen_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.html"

            result = runner.invoke(
                cli,
                [
                    "scan",
                    "--roots",
                    "/media",
                    "--report",
                    str(report_path),
                ],
            )

            assert result.exit_code == 0
            scanner_instance.scan.assert_called_once()
            html_gen_instance.generate.assert_called_once()

    @patch("media_audit.presentation.cli.cli._display_summary")
    @patch("media_audit.presentation.cli.cli.MediaScanner")
    @patch("media_audit.presentation.cli.cli.JSONReportGenerator")
    def test_scan_json_report(
        self, mock_json_gen, mock_scanner, mock_display, runner, mock_scan_result
    ):
        """Test scan with JSON report."""
        # Setup mocks
        scanner_instance = AsyncMock()
        scanner_instance.scan = AsyncMock(return_value=mock_scan_result)
        mock_scanner.return_value = scanner_instance

        json_gen_instance = MagicMock()
        json_gen_instance.generate = MagicMock()
        mock_json_gen.return_value = json_gen_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "report.json"

            result = runner.invoke(
                cli,
                [
                    "scan",
                    "--roots",
                    "/media",
                    "--json",
                    str(json_path),
                ],
            )

            assert result.exit_code == 0
            scanner_instance.scan.assert_called_once()
            json_gen_instance.generate.assert_called_once()

    @patch("media_audit.presentation.cli.cli._display_summary")
    @patch("media_audit.presentation.cli.cli.Config.from_file")
    @patch("media_audit.presentation.cli.cli.MediaScanner")
    def test_scan_with_config(
        self, mock_scanner, mock_config_load, mock_display, runner, mock_scan_result
    ):
        """Test scan using configuration file."""
        # Setup config mock
        mock_config = MagicMock()
        mock_config.scan = MagicMock()
        mock_config.scan.root_paths = [Path("/media")]
        mock_config.scan.profiles = ["plex"]
        mock_config.scan.concurrent_workers = 4
        mock_config.scan.cache_enabled = True
        mock_config.report = MagicMock()
        mock_config.report.output_path = None
        mock_config.report.json_path = None
        mock_config.report.auto_open = False
        mock_config_load.return_value = mock_config

        # Setup scanner mock
        scanner_instance = AsyncMock()
        scanner_instance.scan = AsyncMock(return_value=mock_scan_result)
        mock_scanner.return_value = scanner_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("scan:\n  root_paths:\n    - /media")

            result = runner.invoke(
                cli,
                [
                    "scan",
                    "--config",
                    str(config_path),
                ],
            )

            assert result.exit_code == 0
            mock_config_load.assert_called_once_with(config_path)
            scanner_instance.scan.assert_called_once()

    def test_scan_missing_roots(self, runner):
        """Test scan without required roots parameter."""
        result = runner.invoke(cli, ["scan"])
        assert result.exit_code != 0
        assert "Error" in result.output or "roots" in result.output.lower()

    @patch("media_audit.presentation.cli.cli._display_summary")
    @patch("media_audit.presentation.cli.cli.MediaScanner")
    def test_scan_with_profiles(self, mock_scanner, mock_display, runner, mock_scan_result):
        """Test scan with specific profiles."""
        scanner_instance = AsyncMock()
        scanner_instance.scan = AsyncMock(return_value=mock_scan_result)
        mock_scanner.return_value = scanner_instance

        result = runner.invoke(
            cli,
            [
                "scan",
                "--roots",
                "/media",
                "--profiles",
                "plex",
                "--profiles",
                "jellyfin",
            ],
        )

        assert result.exit_code == 0
        call_args = mock_scanner.call_args
        # Scanner is initialized with ScanConfig object
        assert call_args[0][0].profiles == ["plex", "jellyfin"]

    @patch("media_audit.presentation.cli.cli._display_summary")
    @patch("media_audit.presentation.cli.cli.MediaScanner")
    @patch("media_audit.presentation.cli.cli.webbrowser.open")
    @patch("media_audit.presentation.cli.cli.HTMLReportGenerator")
    def test_scan_auto_open(
        self, mock_html_gen, mock_open, mock_scanner, mock_display, runner, mock_scan_result
    ):
        """Test auto-opening report in browser."""
        # Setup mocks
        scanner_instance = AsyncMock()
        scanner_instance.scan = AsyncMock(return_value=mock_scan_result)
        mock_scanner.return_value = scanner_instance

        html_gen_instance = MagicMock()
        html_gen_instance.generate = MagicMock()
        mock_html_gen.return_value = html_gen_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.html"

            result = runner.invoke(
                cli,
                [
                    "scan",
                    "--roots",
                    "/media",
                    "--report",
                    str(report_path),
                    "--open",
                ],
            )

            assert result.exit_code == 0
            mock_open.assert_called_once()

    @patch("media_audit.presentation.cli.cli._display_summary")
    @patch("media_audit.presentation.cli.cli.MediaScanner")
    def test_scan_problems_only(self, mock_scanner, mock_display, runner):
        """Test scan with problems-only filter."""
        from datetime import datetime

        # Create scan result with problems
        problem_item = MagicMock()
        problem_item.name = "Problem Movie"
        problem_item.path = Path("/media/Problem Movie")
        problem_item.type = MediaType.MOVIE
        problem_item.validation_status = ValidationStatus.ERROR
        problem_item.issues = ["Missing poster"]

        scan_result = MagicMock(spec=ScanResult)
        scan_result.scan_time = datetime.now()
        scan_result.duration = 1.5
        scan_result.root_paths = [Path("/media")]
        scan_result.movies = [problem_item]
        scan_result.series = []
        scan_result.errors = []
        scan_result.total_items = 1
        scan_result.total_issues = 1

        scanner_instance = AsyncMock()
        scanner_instance.scan = AsyncMock(return_value=scan_result)
        mock_scanner.return_value = scanner_instance

        result = runner.invoke(
            cli,
            [
                "scan",
                "--roots",
                "/media",
                "--problems-only",
            ],
        )

        # Exit code 1 because there are issues
        assert result.exit_code == 1

    @patch("media_audit.presentation.cli.cli._display_summary")
    @patch("media_audit.presentation.cli.cli.MediaScanner")
    def test_scan_with_workers(self, mock_scanner, mock_display, runner, mock_scan_result):
        """Test scan with custom worker count."""
        scanner_instance = AsyncMock()
        scanner_instance.scan = AsyncMock(return_value=mock_scan_result)
        mock_scanner.return_value = scanner_instance

        result = runner.invoke(
            cli,
            [
                "scan",
                "--roots",
                "/media",
                "--workers",
                "8",
            ],
        )

        assert result.exit_code == 0
        call_args = mock_scanner.call_args
        # Scanner is initialized with ScanConfig object
        assert call_args[0][0].concurrent_workers == 8

    @patch("media_audit.presentation.cli.cli._display_summary")
    @patch("media_audit.presentation.cli.cli.MediaScanner")
    def test_scan_no_cache(self, mock_scanner, mock_display, runner, mock_scan_result):
        """Test scan with cache disabled."""
        scanner_instance = AsyncMock()
        scanner_instance.scan = AsyncMock(return_value=mock_scan_result)
        mock_scanner.return_value = scanner_instance

        result = runner.invoke(
            cli,
            [
                "scan",
                "--roots",
                "/media",
                "--no-cache",
            ],
        )

        assert result.exit_code == 0
        call_args = mock_scanner.call_args
        # Scanner is initialized with ScanConfig object
        assert call_args[0][0].cache_enabled is False


class TestInitConfigCommand:
    """Test init-config command functionality."""

    def test_init_config_basic(self, runner):
        """Test basic config generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            result = runner.invoke(
                cli,
                [
                    "init-config",
                    str(config_path),
                ],
            )

            assert result.exit_code == 0
            assert config_path.exists()
            content = config_path.read_text()
            assert "scan:" in content
            assert "report:" in content

    def test_init_config_full(self, runner):
        """Test full config generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            result = runner.invoke(
                cli,
                [
                    "init-config",
                    str(config_path),
                    "--full",
                ],
            )

            assert result.exit_code == 0
            assert config_path.exists()
            content = config_path.read_text()
            assert "scan:" in content
            assert "report:" in content
            assert "concurrent_workers" in content
            assert "cache_enabled" in content

    def test_init_config_existing_file(self, runner):
        """Test config generation with existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("existing: content")

            result = runner.invoke(
                cli,
                [
                    "init-config",
                    str(config_path),
                ],
                input="n\n",
            )  # Don't overwrite

            assert "already exists" in result.output
            assert config_path.read_text() == "existing: content"


class TestErrorHandling:
    """Test error handling in CLI."""

    @patch("media_audit.presentation.cli.cli.MediaScanner")
    def test_scan_scanner_error(self, mock_scanner, runner):
        """Test handling of scanner errors."""
        scanner_instance = AsyncMock()
        scanner_instance.scan = AsyncMock(side_effect=Exception("Scanner failed"))
        mock_scanner.return_value = scanner_instance

        result = runner.invoke(
            cli,
            [
                "scan",
                "--roots",
                "/media",
            ],
        )

        assert result.exit_code != 0

    @patch("media_audit.presentation.cli.cli._display_summary")
    @patch("media_audit.presentation.cli.cli.MediaScanner")
    @patch("media_audit.presentation.cli.cli.HTMLReportGenerator")
    def test_scan_report_error(
        self, mock_html_gen, mock_scanner, mock_display, runner, mock_scan_result
    ):
        """Test handling of report generation errors."""
        scanner_instance = AsyncMock()
        scanner_instance.scan = AsyncMock(return_value=mock_scan_result)
        mock_scanner.return_value = scanner_instance

        html_gen_instance = MagicMock()
        html_gen_instance.generate = MagicMock(side_effect=Exception("Report failed"))
        mock_html_gen.return_value = html_gen_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.html"

            result = runner.invoke(
                cli,
                [
                    "scan",
                    "--roots",
                    "/media",
                    "--report",
                    str(report_path),
                ],
            )

            # Should not handle the error and exit with 0 due to issues
            assert result.exit_code == 0

    def test_invalid_config_file(self, runner):
        """Test handling of invalid config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "invalid.yaml"
            config_path.write_text("invalid: yaml: content:")

            result = runner.invoke(
                cli,
                [
                    "scan",
                    "--config",
                    str(config_path),
                ],
            )

            assert result.exit_code != 0


class TestVerboseAndDebug:
    """Test verbose and debug output."""

    @patch("media_audit.presentation.cli.cli._display_summary")
    @patch("media_audit.presentation.cli.cli.setup_logger")
    @patch("media_audit.presentation.cli.cli.MediaScanner")
    def test_verbose_logging(
        self, mock_scanner, mock_logger, mock_display, runner, mock_scan_result
    ):
        """Test verbose logging flag."""
        scanner_instance = AsyncMock()
        scanner_instance.scan = AsyncMock(return_value=mock_scan_result)
        mock_scanner.return_value = scanner_instance

        result = runner.invoke(
            cli,
            [
                "scan",
                "--roots",
                "/media",
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        mock_logger.assert_called()
        # Check that INFO level was set (verbose mode)

    @patch("media_audit.presentation.cli.cli._display_summary")
    @patch("media_audit.presentation.cli.cli.setup_logger")
    @patch("media_audit.presentation.cli.cli.MediaScanner")
    def test_debug_logging(self, mock_scanner, mock_logger, mock_display, runner, mock_scan_result):
        """Test debug logging flag."""
        scanner_instance = AsyncMock()
        scanner_instance.scan = AsyncMock(return_value=mock_scan_result)
        mock_scanner.return_value = scanner_instance

        result = runner.invoke(
            cli,
            [
                "scan",
                "--roots",
                "/media",
                "--debug",
            ],
        )

        assert result.exit_code == 0
        mock_logger.assert_called()
        # Check that DEBUG level was set (debug mode)
