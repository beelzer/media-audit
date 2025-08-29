"""
Base test utilities and helpers for flexible testing.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch


class TestDataBuilder[T]:
    """Generic builder pattern for creating test data flexibly."""

    def __init__(self, model_class: type[T]):
        self._model_class = model_class
        self._data: dict[str, Any] = {}
        self._defaults: dict[str, Any] = {}

    def with_defaults(self, **defaults) -> "TestDataBuilder[T]":
        """Set default values for the builder."""
        self._defaults.update(defaults)
        return self

    def with_field(self, name: str, value: Any) -> "TestDataBuilder[T]":
        """Set a specific field value."""
        self._data[name] = value
        return self

    def with_fields(self, **fields) -> "TestDataBuilder[T]":
        """Set multiple field values."""
        self._data.update(fields)
        return self

    def build(self) -> T:
        """Build the final object."""
        final_data = {**self._defaults, **self._data}
        return self._model_class(**final_data)

    def build_many(self, count: int, vary_field: str | None = None) -> list[T]:
        """Build multiple objects with optional field variation."""
        objects = []
        for i in range(count):
            if vary_field:
                self.with_field(vary_field, f"{self._data.get(vary_field, 'item')}_{i}")
            objects.append(self.build())
        return objects


class FlexibleMock:
    """Flexible mock object that can adapt to interface changes."""

    def __init__(self, spec: type | None = None, **kwargs):
        self._mock = MagicMock(spec=spec) if spec else MagicMock()
        self._configure(**kwargs)

    def _configure(self, **kwargs):
        """Configure mock attributes."""
        for key, value in kwargs.items():
            if callable(value):
                setattr(self._mock, key, value)
            else:
                setattr(self._mock, key, MagicMock(return_value=value))

    def add_method(self, name: str, return_value: Any = None, side_effect: Any = None):
        """Dynamically add a method to the mock."""
        method = MagicMock()
        if return_value is not None:
            method.return_value = return_value
        if side_effect is not None:
            method.side_effect = side_effect
        setattr(self._mock, name, method)
        return self

    def add_property(self, name: str, value: Any):
        """Add a property to the mock."""
        setattr(self._mock, name, value)
        return self

    def get_mock(self) -> MagicMock:
        """Get the underlying mock object."""
        return self._mock


class TestContext:
    """Context manager for test setup and teardown."""

    def __init__(self):
        self._patches: list[Any] = []
        self._cleanup_funcs: list[callable] = []
        self._resources: dict[str, Any] = {}

    def patch(self, target: str, **kwargs) -> Mock:
        """Add a patch to the context."""
        patcher = patch(target, **kwargs)
        mock = patcher.start()
        self._patches.append(patcher)
        return mock

    def add_resource(self, name: str, resource: Any) -> "TestContext":
        """Add a named resource to the context."""
        self._resources[name] = resource
        return self

    def get_resource(self, name: str) -> Any:
        """Get a named resource from the context."""
        return self._resources.get(name)

    def add_cleanup(self, func: callable) -> "TestContext":
        """Add a cleanup function to be called on exit."""
        self._cleanup_funcs.append(func)
        return self

    def __enter__(self) -> "TestContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up all patches and run cleanup functions."""
        for patcher in reversed(self._patches):
            patcher.stop()

        import contextlib
        for cleanup_func in reversed(self._cleanup_funcs):
            with contextlib.suppress(Exception):
                cleanup_func()


@contextmanager
def isolated_test_env(base_path: Path | None = None):
    """Create an isolated test environment."""
    import shutil
    import tempfile

    if base_path is None:
        temp_dir = Path(tempfile.mkdtemp(prefix="media_audit_test_"))
    else:
        temp_dir = base_path / "test_env"
        temp_dir.mkdir(exist_ok=True, parents=True)

    try:
        yield temp_dir
    finally:
        import contextlib
        with contextlib.suppress(Exception):
            shutil.rmtree(temp_dir, ignore_errors=True)


class AsyncTestHelper:
    """Helper for async test scenarios."""

    @staticmethod
    async def gather_with_timeout(*coros, timeout: float = 5.0):
        """Run multiple coroutines with a timeout."""
        import asyncio

        try:
            return await asyncio.wait_for(asyncio.gather(*coros), timeout=timeout)
        except TimeoutError as err:
            raise AssertionError(f"Async operations timed out after {timeout}s") from err

    @staticmethod
    def create_async_mock(return_value: Any = None) -> MagicMock:
        """Create a mock that works with async/await."""
        mock = MagicMock()

        async def async_return():
            return return_value

        mock.return_value = async_return()
        return mock


class DataGenerator:
    """Generate test data dynamically."""

    @staticmethod
    def media_file_path(
        name: str = "test_file",
        year: int = 2024,
        resolution: str = "1080p",
        extension: str = ".mkv",
    ) -> str:
        """Generate a media file path."""
        return f"{name}.{year}.{resolution}{extension}"

    @staticmethod
    def tv_file_path(
        series: str = "Test_Series", season: int = 1, episode: int = 1, extension: str = ".mkv"
    ) -> str:
        """Generate a TV show file path."""
        return f"{series}.S{season:02d}E{episode:02d}{extension}"

    @staticmethod
    def generate_metadata(file_type: str = "movie") -> dict[str, Any]:
        """Generate metadata based on file type."""
        base_metadata = {
            "duration": 7200.0,
            "size": 5368709120,
            "container": "mkv",
        }

        if file_type == "movie":
            base_metadata.update(
                {
                    "title": "Test Movie",
                    "year": 2024,
                    "resolution": "1080p",
                }
            )
        elif file_type == "tv":
            base_metadata.update(
                {
                    "series": "Test Series",
                    "season": 1,
                    "episode": 1,
                }
            )

        return base_metadata


def assert_eventually(
    condition: callable,
    timeout: float = 5.0,
    interval: float = 0.1,
    message: str = "Condition not met within timeout",
):
    """Assert that a condition becomes true within a timeout."""
    import time

    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition():
            return
        time.sleep(interval)

    raise AssertionError(message)
