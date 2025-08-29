"""Cross-platform utilities for media-audit.

Provides consistent cross-platform behavior for paths, directories,
and system operations.
"""

from __future__ import annotations

import asyncio
import os
import platform
import sys
from collections.abc import Coroutine
from pathlib import Path
from typing import Any


def get_cache_dir() -> Path:
    """Get the appropriate cache directory for the current platform.

    Returns:
        Path: Platform-specific cache directory
        - Windows: %LOCALAPPDATA%/media-audit/cache or %APPDATA%/media-audit/cache
        - macOS: ~/Library/Caches/media-audit
        - Linux/Unix: ~/.cache/media-audit
    """
    if sys.platform == "win32":
        # Windows: Use LOCALAPPDATA (preferred) or APPDATA
        local_app = os.environ.get("LOCALAPPDATA")
        if local_app:
            return Path(local_app) / "media-audit" / "cache"

        app_data = os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / "media-audit" / "cache"

        # Fallback to home directory
        return Path.home() / "AppData" / "Local" / "media-audit" / "cache"

    elif sys.platform == "darwin":
        # macOS: Use ~/Library/Caches
        return Path.home() / "Library" / "Caches" / "media-audit"

    else:
        # Linux/Unix: Use XDG_CACHE_HOME or ~/.cache
        cache_home = os.environ.get("XDG_CACHE_HOME")
        if cache_home:
            return Path(cache_home) / "media-audit"
        return Path.home() / ".cache" / "media-audit"


def get_config_dir() -> Path:
    """Get the appropriate configuration directory for the current platform.

    Returns:
        Path: Platform-specific config directory
        - Windows: %APPDATA%/media-audit
        - macOS: ~/Library/Application Support/media-audit
        - Linux/Unix: ~/.config/media-audit
    """
    if sys.platform == "win32":
        # Windows: Use APPDATA
        app_data = os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / "media-audit"
        # Fallback
        return Path.home() / "AppData" / "Roaming" / "media-audit"

    elif sys.platform == "darwin":
        # macOS: Use ~/Library/Application Support
        return Path.home() / "Library" / "Application Support" / "media-audit"

    else:
        # Linux/Unix: Use XDG_CONFIG_HOME or ~/.config
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            return Path(config_home) / "media-audit"
        return Path.home() / ".config" / "media-audit"


def is_windows() -> bool:
    """Check if running on Windows.

    Returns:
        bool: True if running on Windows
    """
    return sys.platform == "win32"


def is_macos() -> bool:
    """Check if running on macOS.

    Returns:
        bool: True if running on macOS
    """
    return sys.platform == "darwin"


def is_linux() -> bool:
    """Check if running on Linux.

    Returns:
        bool: True if running on Linux
    """
    return sys.platform.startswith("linux")


def get_architecture() -> str:
    """Get the system architecture.

    Returns:
        str: Architecture string (e.g., 'x86_64', 'arm64', 'aarch64')
    """
    return platform.machine().lower()


def is_arm() -> bool:
    """Check if running on ARM architecture.

    Returns:
        bool: True if running on ARM (arm64, aarch64, armv7l, etc.)
    """
    arch = get_architecture()
    return any(arm_id in arch for arm_id in ["arm", "aarch"])


def is_x86() -> bool:
    """Check if running on x86/x64 architecture.

    Returns:
        bool: True if running on x86 or x64
    """
    arch = get_architecture()
    return any(x86_id in arch for x86_id in ["x86", "x64", "amd64", "i386", "i686"])


def get_platform_info() -> dict[str, str]:
    """Get comprehensive platform information.

    Returns:
        dict: Platform details including OS, architecture, Python version
    """
    return {
        "system": platform.system(),
        "platform": sys.platform,
        "architecture": get_architecture(),
        "processor": platform.processor() or "unknown",
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "is_arm": str(is_arm()),
        "is_x86": str(is_x86()),
        "is_64bit": str(sys.maxsize > 2**32),
    }


def normalize_path(path: Path | str) -> Path:
    """Normalize a path for the current platform.

    Resolves symlinks, expands ~ and environment variables, and ensures
    consistent path separators.

    Args:
        path: Path to normalize

    Returns:
        Path: Normalized path
    """
    if isinstance(path, str):
        path = Path(path)

    # Expand ~ and environment variables
    path_str = os.path.expanduser(os.path.expandvars(str(path)))
    path = Path(path_str)

    # Resolve to absolute path
    try:
        path = path.resolve()
    except (OSError, RuntimeError):
        # If resolve fails (e.g., on some network drives on Windows),
        # just make it absolute
        path = path.absolute()

    return path


def setup_asyncio_policy() -> None:
    """Setup platform-specific asyncio event loop policy.

    Configures the appropriate event loop policy for the current platform
    to avoid issues with subprocess handling and signal management.
    ARM platforms may need specific tuning for optimal performance.
    """
    if sys.platform == "win32":
        # Windows: Use ProactorEventLoop for better subprocess support
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    elif is_arm() and is_linux():
        # ARM Linux: May benefit from specific event loop tuning
        # Currently using default, but can be optimized based on testing
        pass


def get_optimal_worker_count() -> int:
    """Get optimal worker count for the current platform and architecture.

    ARM platforms may benefit from different concurrency settings
    compared to x86 platforms.

    Returns:
        int: Optimal number of concurrent workers
    """
    cpu_count = os.cpu_count() or 4

    if is_arm():
        # ARM processors often have better power efficiency
        # but may benefit from slightly lower concurrency
        if is_macos():
            # Apple Silicon has excellent performance
            return min(cpu_count, 8)
        else:
            # Other ARM platforms (Raspberry Pi, etc.)
            return min(cpu_count, 4)
    else:
        # x86/x64 platforms
        return min(cpu_count, 8)


def run_async[T](coro: Coroutine[Any, Any, T], *, suppress_warnings: bool = True) -> T:
    """Run an async coroutine with platform-specific configuration.

    Args:
        coro: Coroutine to run
        suppress_warnings: Whether to suppress common platform-specific warnings

    Returns:
        The result of the coroutine
    """
    if sys.platform == "win32":
        # Windows-specific configuration
        setup_asyncio_policy()

        if suppress_warnings:
            # Create custom event loop with exception handler
            loop = asyncio.new_event_loop()

            def exception_handler(loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
                """Suppress common Windows asyncio warnings."""
                exception = context.get("exception")
                if exception and "I/O operation on closed pipe" in str(exception):
                    return  # Suppress ProactorBasePipeTransport errors

                message = context.get("message", "")
                if message and any(
                    msg in message
                    for msg in [
                        "unclosed transport",
                        "Task was destroyed but it is pending",
                        "Task exception was never retrieved",
                    ]
                ):
                    return  # Suppress cleanup messages

                # Log other exceptions
                import logging

                logging.getLogger("asyncio").error(f"Unhandled exception: {context}")

            loop.set_exception_handler(exception_handler)
            asyncio.set_event_loop(loop)

            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        else:
            # Run normally without suppression
            return asyncio.run(coro)
    else:
        # Unix/Linux/macOS: Run normally
        return asyncio.run(coro)
