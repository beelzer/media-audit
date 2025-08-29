"""
Test helpers for common testing patterns.
"""

import asyncio
import functools
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar
from unittest.mock import MagicMock, patch

T = TypeVar("T")


def retry_test(times: int = 3, delay: float = 0.1):
    """Decorator to retry flaky tests."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < times - 1:
                        import time

                        time.sleep(delay)
            raise last_exception

        return wrapper

    return decorator


def skip_on_windows(reason: str = "Not supported on Windows"):
    """Skip test on Windows platform."""
    import pytest

    return pytest.mark.skipif(sys.platform == "win32", reason=reason)


def skip_on_ci(reason: str = "Skipped in CI environment"):
    """Skip test in CI environment."""
    import os

    import pytest

    return pytest.mark.skipif(os.environ.get("CI") == "true", reason=reason)


def requires_ffmpeg(func):
    """Decorator to skip tests that require ffmpeg."""
    import shutil

    import pytest

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not shutil.which("ffmpeg"):
            pytest.skip("ffmpeg not available")
        return func(*args, **kwargs)

    return wrapper


class AsyncTestRunner:
    """Helper for running async tests with proper cleanup."""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.tasks: list[asyncio.Task] = []

    async def run(self, coro):
        """Run a coroutine and track it."""
        task = asyncio.create_task(coro)
        self.tasks.append(task)

        try:
            return await asyncio.wait_for(task, timeout=self.timeout)
        except TimeoutError:
            task.cancel()
            raise

    async def cleanup(self):
        """Cancel all pending tasks."""
        for task in self.tasks:
            if not task.done():
                task.cancel()
                import contextlib
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        self.tasks.clear()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.cleanup()


def mock_async_iter(items: list):
    """Create an async iterator from a list."""

    async def _iter():
        for item in items:
            yield item

    return _iter()


def capture_logs(logger_name: str = None):
    """Context manager to capture log messages."""
    import logging
    from io import StringIO

    class LogCapture:
        def __init__(self):
            self.stream = StringIO()
            self.handler = logging.StreamHandler(self.stream)
            self.logger = None
            self.original_level = None

        def __enter__(self):
            if logger_name:
                self.logger = logging.getLogger(logger_name)
            else:
                self.logger = logging.getLogger()

            self.original_level = self.logger.level
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(self.handler)
            return self

        def __exit__(self, *args):
            self.logger.removeHandler(self.handler)
            self.logger.setLevel(self.original_level)

        def get_output(self) -> str:
            return self.stream.getvalue()

        def contains(self, text: str) -> bool:
            return text in self.get_output()

    return LogCapture()


class TempEnvironment:
    """Temporarily modify environment variables."""

    def __init__(self, **env_vars):
        self.env_vars = env_vars
        self.original = {}

    def __enter__(self):
        import os

        for key, value in self.env_vars.items():
            self.original[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = str(value)
        return self

    def __exit__(self, *args):
        import os

        for key, original_value in self.original.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


def assert_files_equal(file1: Path, file2: Path, ignore_lines: list[str] = None):
    """Assert two files have identical content."""
    content1 = file1.read_text()
    content2 = file2.read_text()

    if ignore_lines:
        lines1 = [
            line for line in content1.splitlines() if not any(ignore in line for ignore in ignore_lines)
        ]
        lines2 = [
            line for line in content2.splitlines() if not any(ignore in line for ignore in ignore_lines)
        ]
        content1 = "\n".join(lines1)
        content2 = "\n".join(lines2)

    assert content1 == content2, f"Files {file1} and {file2} differ"


def create_mock_with_spec(spec_class: type, **attributes) -> MagicMock:
    """Create a mock with proper spec and attributes."""
    mock = MagicMock(spec=spec_class)

    for attr, value in attributes.items():
        if callable(value):
            setattr(mock, attr, MagicMock(side_effect=value))
        else:
            setattr(mock, attr, value)

    return mock


class PatchManager:
    """Manage multiple patches in tests."""

    def __init__(self):
        self.patches = {}
        self.mocks = {}

    def add(self, name: str, target: str, **kwargs):
        """Add a patch."""
        self.patches[name] = patch(target, **kwargs)
        return self

    def start_all(self):
        """Start all patches."""
        for name, patcher in self.patches.items():
            self.mocks[name] = patcher.start()
        return self.mocks

    def stop_all(self):
        """Stop all patches."""
        for patcher in self.patches.values():
            patcher.stop()
        self.patches.clear()
        self.mocks.clear()

    def __enter__(self):
        return self.start_all()

    def __exit__(self, *args):
        self.stop_all()


def wait_for_condition(
    condition: Callable[[], bool], timeout: float = 5.0, interval: float = 0.1, message: str = None
):
    """Wait for a condition to become true."""
    import time

    start = time.time()
    while time.time() - start < timeout:
        if condition():
            return
        time.sleep(interval)

    raise TimeoutError(message or f"Condition not met within {timeout}s")


def generate_test_id(obj: Any) -> str:
    """Generate a readable test ID from an object."""
    if isinstance(obj, dict):
        return "_".join(f"{k}={v}" for k, v in obj.items())
    elif isinstance(obj, list | tuple):
        return "_".join(str(item) for item in obj)
    else:
        return str(obj).replace(" ", "_").replace("/", "_")


class ExceptionContext:
    """Enhanced exception assertion context."""

    def __init__(self, exception_type: type[Exception], match: str = None):
        self.exception_type = exception_type
        self.match = match
        self.exception = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            raise AssertionError(
                f"Expected {self.exception_type.__name__} but no exception was raised"
            )

        if not issubclass(exc_type, self.exception_type):
            return False

        self.exception = exc_val

        if self.match and self.match not in str(exc_val):
            raise AssertionError(f"Exception message '{exc_val}' does not contain '{self.match}'")

        return True
