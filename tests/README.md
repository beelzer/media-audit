# Media-Audit Test Suite

## Overview

This test suite provides a comprehensive and flexible testing foundation for the media-audit project.

## Structure

```
tests/
├── conftest.py          # Shared fixtures and pytest configuration
├── unit/                # Unit tests for individual components
├── integration/         # Integration tests for component interactions
├── fixtures/            # Test data and file fixtures
└── utils/               # Testing utilities and helpers
    ├── base.py          # Base test utilities and builders
    ├── factories.py     # Object factories for test data
    ├── assertions.py    # Custom assertions and matchers
    └── mocks.py        # Reusable mock objects
```

## Key Features

### 1. Flexible Test Data Generation

- **Factory Pattern**: Use factories to create test objects with sensible defaults
- **Builder Pattern**: Build complex test data incrementally
- **Dynamic Generation**: Generate test data based on parameters

### 2. Comprehensive Assertions

- **Domain-Specific**: Custom assertions for media files, scan results, etc.
- **Flexible Comparison**: Compare objects while ignoring specific fields
- **Async Support**: Assertions for async operations with timeout handling

### 3. Reusable Mock Objects

- **Smart Mocks**: Mocks that track calls and provide statistics
- **Configurable**: Easy to configure behavior and responses
- **Resetable**: Clean state between tests

### 4. Test Isolation

- **Isolated Environments**: Create isolated test environments
- **Resource Management**: Automatic cleanup of test resources
- **Context Managers**: Clean setup and teardown

## Usage Examples

### Using Factories

```python
from tests.utils.factories import MediaFileFactory, StreamFactory

def test_media_file():
    # Create with defaults
    file = MediaFileFactory.create()

    # Create with custom values
    file = MediaFileFactory.create(
        title="Custom Movie",
        year=2025,
        resolution="4K"
    )

    # Create batch with variations
    files = MediaFileFactory.create_batch(
        count=10,
        vary_fields={"resolution": ["720p", "1080p", "4K"]}
    )
```

### Using Custom Assertions

```python
from tests.utils.assertions import MediaFileAssertions, ScanResultAssertions

def test_scan_result(result):
    # Validate scan result
    ScanResultAssertions.assert_valid_scan_result(result)

    # Check specific stats
    ScanResultAssertions.assert_scan_stats_match(
        result,
        expected_processed=10,
        expected_failed=0
    )

    # Validate media files
    for file in result.media_files:
        MediaFileAssertions.assert_valid_media_file(file)
```

### Using Mock Objects

```python
from tests.utils.mocks import MockFFProbe, MockCache

def test_with_mocks():
    # Setup FFProbe mock
    mock_probe = MockFFProbe()
    mock_probe.set_response("/path/to/file.mkv", custom_response)
    mock_probe.set_error("/path/to/bad.mkv", Exception("Probe failed"))

    # Setup Cache mock
    mock_cache = MockCache()
    mock_cache.set("key", "value")

    # Check statistics
    stats = mock_cache.get_stats()
    assert stats["hits"] == 1
```

### Using Test Builders

```python
from tests.utils.base import TestDataBuilder

def test_with_builder():
    builder = TestDataBuilder(MediaFile)
    builder.with_defaults(
        container="mkv",
        duration=7200.0
    )

    file1 = builder.with_field("title", "Movie 1").build()
    file2 = builder.with_field("title", "Movie 2").build()
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/media_audit

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_models.py

# Run with parallel execution
pytest -n auto
```

## Writing New Tests

### Unit Test Template

```python
import pytest
from tests.utils.factories import MediaFileFactory
from tests.utils.assertions import MediaFileAssertions

class TestNewFeature:
    """Tests for new feature."""

    def test_basic_functionality(self):
        """Test basic feature functionality."""
        # Arrange
        test_file = MediaFileFactory.create()

        # Act
        result = process_feature(test_file)

        # Assert
        assert result is not None
        MediaFileAssertions.assert_valid_media_file(result)

    @pytest.mark.parametrize("input_val,expected", [
        ("test1", "result1"),
        ("test2", "result2"),
    ])
    def test_with_parameters(self, input_val, expected):
        """Test with different parameters."""
        result = feature_function(input_val)
        assert result == expected
```

### Integration Test Template

```python
import pytest
from tests.utils.base import isolated_test_env
from tests.utils.mocks import MockFFProbe

@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration():
    """Test component integration."""
    async with isolated_test_env() as test_dir:
        # Setup test environment
        mock_probe = MockFFProbe()

        # Run integration test
        result = await scan_directory(test_dir)

        # Verify results
        assert result.processed_files > 0
```

## Best Practices

1. **Use Factories**: Prefer factories over manual object creation
2. **Mock External Dependencies**: Always mock FFProbe, file system, etc.
3. **Test Isolation**: Each test should be independent
4. **Clear Assertions**: Use domain-specific assertions for clarity
5. **Parametrize Tests**: Use pytest.mark.parametrize for multiple scenarios
6. **Mark Tests**: Use markers (unit, integration, slow) appropriately
7. **Clean State**: Reset mocks and clear resources after tests
