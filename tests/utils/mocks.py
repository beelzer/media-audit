"""
Reusable mock objects and mock factories for testing.
"""

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock


class MockFFProbe:
    """Mock FFProbe implementation for testing."""

    def __init__(self, default_response: dict[str, Any] | None = None):
        self.default_response = default_response or self._get_default_response()
        self.call_count = 0
        self.called_with: list[str] = []
        self.responses: dict[str, dict] = {}
        self.errors: dict[str, Exception] = {}
        self.delay: float = 0.0

    def _get_default_response(self) -> dict[str, Any]:
        """Get default FFProbe response."""
        return {
            "format": {
                "filename": "test.mkv",
                "format_name": "matroska,webm",
                "duration": "7200.000000",
                "size": "5368709120",
            },
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                },
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "channels": 2,
                },
            ],
        }

    def set_response(self, file_path: str, response: dict[str, Any]):
        """Set a specific response for a file path."""
        self.responses[file_path] = response

    def set_error(self, file_path: str, error: Exception):
        """Set an error to be raised for a specific file path."""
        self.errors[file_path] = error

    def set_delay(self, delay: float):
        """Set a delay for all probe operations."""
        self.delay = delay

    async def probe(self, file_path: str) -> dict[str, Any]:
        """Mock probe method."""
        self.call_count += 1
        self.called_with.append(file_path)

        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if file_path in self.errors:
            raise self.errors[file_path]

        if file_path in self.responses:
            return self.responses[file_path]

        return self.default_response

    def reset(self):
        """Reset the mock state."""
        self.call_count = 0
        self.called_with = []
        self.responses = {}
        self.errors = {}
        self.delay = 0.0


class MockCache:
    """Mock cache implementation for testing."""

    def __init__(self):
        self.store: dict[str, Any] = {}
        self.get_count = 0
        self.set_count = 0
        self.hits = 0
        self.misses = 0
        self.enabled = True

    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        self.get_count += 1

        if not self.enabled:
            self.misses += 1
            return None

        if key in self.store:
            self.hits += 1
            return self.store[key]

        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl: int | None = None):
        """Set a value in cache."""
        self.set_count += 1

        if self.enabled:
            self.store[key] = value

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self.store if self.enabled else False

    def clear(self):
        """Clear the cache."""
        self.store.clear()

    def disable(self):
        """Disable the cache."""
        self.enabled = False

    def enable(self):
        """Enable the cache."""
        self.enabled = True

    def reset(self):
        """Reset the mock state."""
        self.store.clear()
        self.get_count = 0
        self.set_count = 0
        self.hits = 0
        self.misses = 0
        self.enabled = True

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {
            "gets": self.get_count,
            "sets": self.set_count,
            "hits": self.hits,
            "misses": self.misses,
            "size": len(self.store),
        }


class MockFileSystem:
    """Mock file system for testing."""

    def __init__(self, base_path: Path | None = None):
        self.base_path = base_path or Path("/test")
        self.files: dict[Path, dict[str, Any]] = {}
        self.directories: set[Path] = {self.base_path}

    def add_file(
        self,
        path: Path | str,
        size: int = 1024,
        content: str | bytes | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Add a file to the mock file system."""
        path = Path(path) if isinstance(path, str) else path
        if not path.is_absolute():
            path = self.base_path / path

        self.files[path] = {
            "size": size,
            "content": content,
            "metadata": metadata or {},
        }

        self.directories.add(path.parent)

    def add_directory(self, path: Path | str):
        """Add a directory to the mock file system."""
        path = Path(path) if isinstance(path, str) else path
        if not path.is_absolute():
            path = self.base_path / path

        self.directories.add(path)

    def exists(self, path: Path | str) -> bool:
        """Check if a path exists."""
        path = Path(path) if isinstance(path, str) else path
        if not path.is_absolute():
            path = self.base_path / path

        return path in self.files or path in self.directories

    def is_file(self, path: Path | str) -> bool:
        """Check if a path is a file."""
        path = Path(path) if isinstance(path, str) else path
        if not path.is_absolute():
            path = self.base_path / path

        return path in self.files

    def is_dir(self, path: Path | str) -> bool:
        """Check if a path is a directory."""
        path = Path(path) if isinstance(path, str) else path
        if not path.is_absolute():
            path = self.base_path / path

        return path in self.directories

    def list_dir(self, path: Path | str) -> list[Path]:
        """List contents of a directory."""
        path = Path(path) if isinstance(path, str) else path
        if not path.is_absolute():
            path = self.base_path / path

        if path not in self.directories:
            raise FileNotFoundError(f"Directory not found: {path}")

        contents = []

        for file_path in self.files:
            if file_path.parent == path:
                contents.append(file_path)

        for dir_path in self.directories:
            if dir_path.parent == path and dir_path != path:
                contents.append(dir_path)

        return contents

    def get_size(self, path: Path | str) -> int:
        """Get the size of a file."""
        path = Path(path) if isinstance(path, str) else path
        if not path.is_absolute():
            path = self.base_path / path

        if path in self.files:
            return self.files[path]["size"]

        raise FileNotFoundError(f"File not found: {path}")

    def reset(self):
        """Reset the mock file system."""
        self.files.clear()
        self.directories = {self.base_path}


class MockProgressBar:
    """Mock progress bar for testing."""

    def __init__(self, total: int = 100):
        self.total = total
        self.current = 0
        self.description = ""
        self.updates: list[int] = []
        self.descriptions: list[str] = []
        self.closed = False

    def update(self, advance: int = 1):
        """Update progress."""
        self.current += advance
        self.updates.append(advance)

    def set_description(self, description: str):
        """Set progress description."""
        self.description = description
        self.descriptions.append(description)

    def refresh(self):
        """Refresh the progress bar."""
        pass

    def close(self):
        """Close the progress bar."""
        self.closed = True

    def reset(self):
        """Reset the progress bar."""
        self.current = 0
        self.description = ""
        self.updates = []
        self.descriptions = []
        self.closed = False


class MockLogger:
    """Mock logger for testing."""

    def __init__(self):
        self.messages: dict[str, list[str]] = {
            "debug": [],
            "info": [],
            "warning": [],
            "error": [],
            "critical": [],
        }

    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.messages["debug"].append(message)

    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.messages["info"].append(message)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.messages["warning"].append(message)

    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.messages["error"].append(message)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self.messages["critical"].append(message)

    def has_message(self, level: str, message: str) -> bool:
        """Check if a message was logged at a specific level."""
        return message in self.messages.get(level, [])

    def get_messages(self, level: str | None = None) -> list[str]:
        """Get logged messages."""
        if level:
            return self.messages.get(level, [])

        all_messages = []
        for msgs in self.messages.values():
            all_messages.extend(msgs)
        return all_messages

    def reset(self):
        """Reset the logger."""
        for level in self.messages:
            self.messages[level] = []


def create_async_context_manager(enter_value: Any = None, exit_value: Any = None) -> AsyncMock:
    """Create an async context manager mock."""
    mock = AsyncMock()
    mock.__aenter__ = AsyncMock(return_value=enter_value)
    mock.__aexit__ = AsyncMock(return_value=exit_value)
    return mock


def create_mock_scanner(result: Any | None = None, error: Exception | None = None) -> Mock:
    """Create a mock scanner."""
    mock = Mock()

    if error:
        mock.scan = Mock(side_effect=error)
        mock.scan_async = AsyncMock(side_effect=error)
    else:
        mock.scan = Mock(return_value=result)
        mock.scan_async = AsyncMock(return_value=result)

    return mock
