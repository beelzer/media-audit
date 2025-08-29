"""Tests for platform utilities."""

from pathlib import Path
from unittest.mock import patch

from media_audit.shared.platform_utils import (
    get_architecture,
    get_cache_dir,
    get_config_dir,
    get_optimal_worker_count,
    get_platform_info,
    is_arm,
    is_linux,
    is_macos,
    is_windows,
    is_x86,
    normalize_path,
)


class TestPlatformDetection:
    """Test platform detection functions."""

    def test_is_windows(self):
        """Test Windows detection."""
        with patch("sys.platform", "win32"):
            assert is_windows() is True
        with patch("sys.platform", "linux"):
            assert is_windows() is False
        with patch("sys.platform", "darwin"):
            assert is_windows() is False

    def test_is_macos(self):
        """Test macOS detection."""
        with patch("sys.platform", "darwin"):
            assert is_macos() is True
        with patch("sys.platform", "win32"):
            assert is_macos() is False
        with patch("sys.platform", "linux"):
            assert is_macos() is False

    def test_is_linux(self):
        """Test Linux detection."""
        with patch("sys.platform", "linux"):
            assert is_linux() is True
        with patch("sys.platform", "linux2"):
            assert is_linux() is True
        with patch("sys.platform", "win32"):
            assert is_linux() is False

    def test_get_architecture(self):
        """Test architecture detection."""
        with patch("platform.machine") as mock_machine:
            mock_machine.return_value = "x86_64"
            assert get_architecture() == "x86_64"

            mock_machine.return_value = "ARM64"
            assert get_architecture() == "arm64"

            mock_machine.return_value = "aarch64"
            assert get_architecture() == "aarch64"

    def test_is_arm(self):
        """Test ARM detection."""
        with patch("platform.machine") as mock_machine:
            # ARM variants
            mock_machine.return_value = "arm64"
            assert is_arm() is True

            mock_machine.return_value = "aarch64"
            assert is_arm() is True

            mock_machine.return_value = "armv7l"
            assert is_arm() is True

            mock_machine.return_value = "armv6l"
            assert is_arm() is True

            # Non-ARM
            mock_machine.return_value = "x86_64"
            assert is_arm() is False

            mock_machine.return_value = "i686"
            assert is_arm() is False

    def test_is_x86(self):
        """Test x86 detection."""
        with patch("platform.machine") as mock_machine:
            # x86 variants
            mock_machine.return_value = "x86_64"
            assert is_x86() is True

            mock_machine.return_value = "amd64"
            assert is_x86() is True

            mock_machine.return_value = "i386"
            assert is_x86() is True

            mock_machine.return_value = "i686"
            assert is_x86() is True

            # Non-x86
            mock_machine.return_value = "arm64"
            assert is_x86() is False

            mock_machine.return_value = "aarch64"
            assert is_x86() is False

    def test_get_platform_info(self):
        """Test comprehensive platform info."""
        info = get_platform_info()

        # Check required keys
        assert "system" in info
        assert "platform" in info
        assert "architecture" in info
        assert "processor" in info
        assert "python_version" in info
        assert "python_implementation" in info
        assert "is_arm" in info
        assert "is_x86" in info
        assert "is_64bit" in info

        # Check types
        assert isinstance(info["system"], str)
        assert isinstance(info["platform"], str)
        assert isinstance(info["architecture"], str)
        assert isinstance(info["python_version"], str)
        assert info["is_arm"] in ["True", "False"]
        assert info["is_x86"] in ["True", "False"]
        assert info["is_64bit"] in ["True", "False"]


class TestDirectoryFunctions:
    """Test platform-specific directory functions."""

    def test_get_cache_dir_windows(self):
        """Test Windows cache directory."""
        with (
            patch("sys.platform", "win32"),
            patch.dict("os.environ", {"LOCALAPPDATA": r"C:\Users\Test\AppData\Local"}),
        ):
            cache_dir = get_cache_dir()
            assert "media-audit" in str(cache_dir)
            assert "cache" in str(cache_dir)

    def test_get_cache_dir_macos(self):
        """Test macOS cache directory."""
        with patch("sys.platform", "darwin"), patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/Users/test")
            cache_dir = get_cache_dir()
            expected = Path("/Users/test/Library/Caches/media-audit")
            assert cache_dir == expected

    def test_get_cache_dir_linux(self):
        """Test Linux cache directory."""
        with (
            patch("sys.platform", "linux"),
            patch("pathlib.Path.home") as mock_home,
            patch.dict("os.environ", {}, clear=True),
        ):
            mock_home.return_value = Path("/home/test")
            cache_dir = get_cache_dir()
            expected = Path("/home/test/.cache/media-audit")
            assert cache_dir == expected

    def test_get_cache_dir_linux_xdg(self):
        """Test Linux cache directory with XDG_CACHE_HOME."""
        with (
            patch("sys.platform", "linux"),
            patch.dict("os.environ", {"XDG_CACHE_HOME": "/custom/cache"}),
        ):
            cache_dir = get_cache_dir()
            expected = Path("/custom/cache/media-audit")
            assert cache_dir == expected

    def test_get_config_dir_windows(self):
        """Test Windows config directory."""
        with (
            patch("sys.platform", "win32"),
            patch.dict("os.environ", {"APPDATA": r"C:\Users\Test\AppData\Roaming"}),
        ):
            config_dir = get_config_dir()
            assert "media-audit" in str(config_dir)
            assert "Roaming" in str(config_dir)

    def test_get_config_dir_macos(self):
        """Test macOS config directory."""
        with patch("sys.platform", "darwin"), patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/Users/test")
            config_dir = get_config_dir()
            expected = Path("/Users/test/Library/Application Support/media-audit")
            assert config_dir == expected

    def test_get_config_dir_linux(self):
        """Test Linux config directory."""
        with (
            patch("sys.platform", "linux"),
            patch("pathlib.Path.home") as mock_home,
            patch.dict("os.environ", {}, clear=True),
        ):
            mock_home.return_value = Path("/home/test")
            config_dir = get_config_dir()
            expected = Path("/home/test/.config/media-audit")
            assert config_dir == expected


class TestWorkerOptimization:
    """Test worker count optimization."""

    def test_get_optimal_worker_count_arm_macos(self):
        """Test worker count for ARM macOS."""
        with (
            patch("platform.machine") as mock_machine,
            patch("sys.platform", "darwin"),
            patch("os.cpu_count") as mock_cpu,
        ):
            mock_machine.return_value = "arm64"
            mock_cpu.return_value = 10
            assert get_optimal_worker_count() == 8  # Max 8 for Apple Silicon

            mock_cpu.return_value = 4
            assert get_optimal_worker_count() == 4

    def test_get_optimal_worker_count_arm_linux(self):
        """Test worker count for ARM Linux."""
        with (
            patch("platform.machine") as mock_machine,
            patch("sys.platform", "linux"),
            patch("os.cpu_count") as mock_cpu,
        ):
            mock_machine.return_value = "aarch64"
            mock_cpu.return_value = 8
            assert get_optimal_worker_count() == 4  # Max 4 for ARM Linux

            mock_cpu.return_value = 2
            assert get_optimal_worker_count() == 2

    def test_get_optimal_worker_count_x86(self):
        """Test worker count for x86."""
        with patch("platform.machine") as mock_machine, patch("os.cpu_count") as mock_cpu:
            mock_machine.return_value = "x86_64"
            mock_cpu.return_value = 16
            assert get_optimal_worker_count() == 8  # Max 8 for x86

            mock_cpu.return_value = 4
            assert get_optimal_worker_count() == 4

    def test_get_optimal_worker_count_fallback(self):
        """Test worker count fallback when cpu_count is None."""
        with patch("os.cpu_count") as mock_cpu:
            mock_cpu.return_value = None
            count = get_optimal_worker_count()
            assert count == 4  # Default fallback


class TestPathNormalization:
    """Test path normalization."""

    def test_normalize_path_string(self):
        """Test normalizing string paths."""
        path = normalize_path(".")
        assert isinstance(path, Path)
        assert path.is_absolute()

    def test_normalize_path_object(self):
        """Test normalizing Path objects."""
        path = normalize_path(Path("."))
        assert isinstance(path, Path)
        assert path.is_absolute()

    def test_normalize_path_expanduser(self):
        """Test tilde expansion."""
        with patch("os.path.expanduser") as mock_expand:
            mock_expand.return_value = "/home/test/path"
            _ = normalize_path("~/path")
            mock_expand.assert_called_once()

    def test_normalize_path_expandvars(self):
        """Test environment variable expansion."""
        with (
            patch.dict("os.environ", {"TEST_VAR": "/test/value"}),
            patch("os.path.expandvars") as mock_expand,
        ):
            mock_expand.return_value = "/test/value/path"
            _ = normalize_path("$TEST_VAR/path")
            mock_expand.assert_called_once()
