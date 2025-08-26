# Testing Guide

This guide covers the testing strategy, practices, and tools used in Media Audit development.

## Overview

Media Audit uses a comprehensive testing approach to ensure code quality, reliability, and maintainability. Our testing strategy includes:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Property-Based Tests**: Test with generated inputs
- **Performance Tests**: Validate performance requirements

## Testing Framework

### Pytest

We use [Pytest](https://pytest.org/) as our primary testing framework for its:

- Simple and readable syntax
- Powerful fixture system
- Extensive plugin ecosystem
- Detailed failure reporting
- Parametrization support

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_patterns.py
│   ├── test_parsers/
│   │   ├── test_base_parser.py
│   │   ├── test_movie_parser.py
│   │   └── test_tv_parser.py
│   ├── test_validator.py
│   └── test_cache.py
├── integration/             # Integration tests
│   ├── test_scanner.py
│   ├── test_end_to_end.py
│   └── test_report_generation.py
├── fixtures/                # Test data fixtures
│   ├── movies/
│   └── tv/
└── performance/             # Performance tests
    └── test_large_library.py
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run specific test file
pytest tests/unit/test_config.py

# Run specific test function
pytest tests/unit/test_config.py::test_config_validation

# Run tests matching pattern
pytest -k "test_movie"

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l
```

### Coverage Reporting

```bash
# Run tests with coverage
pytest --cov=src

# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Generate XML coverage report (for CI)
pytest --cov=src --cov-report=xml

# Show missing lines
pytest --cov=src --cov-report=term-missing

# Set coverage threshold
pytest --cov=src --cov-fail-under=90
```

### Test Filtering

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Skip slow tests
pytest -m "not slow"

# Run only tests marked as 'fast'
pytest -m fast

# Run tests by custom markers
pytest -m "parser and not slow"
```

## Writing Tests

### Test Naming Conventions

- **Test Files**: `test_*.py` or `*_test.py`
- **Test Functions**: `test_*` prefix
- **Test Classes**: `Test*` prefix
- **Descriptive Names**: Use descriptive, specific names

```python
# Good test names
def test_movie_parser_extracts_title_from_directory_name():
    pass

def test_validator_reports_error_when_poster_missing():
    pass

def test_cache_invalidates_entry_when_file_modified():
    pass

# Less descriptive names (avoid)
def test_parser():
    pass

def test_validation():
    pass
```

### Test Organization

#### Arrange-Act-Assert Pattern

Organize tests using the AAA pattern:

```python
def test_movie_parser_parses_valid_directory():
    # Arrange - Set up test data and conditions
    directory = Path("/movies/The Matrix (1999)")
    patterns = get_test_patterns()
    parser = MovieParser(patterns)
    
    # Act - Execute the function being tested
    result = parser.parse(directory)
    
    # Assert - Verify the expected outcome
    assert result is not None
    assert result.name == "The Matrix"
    assert result.year == 1999
    assert result.type == MediaType.MOVIE
```

#### Given-When-Then Pattern

Alternative organization for behavior-driven tests:

```python
def test_cache_returns_none_for_missing_entry():
    # Given: A cache with no entries
    cache = MediaCache(enabled=True)
    missing_path = Path("/nonexistent/file.mkv")
    
    # When: Requesting data for non-existent file
    result = cache.get_probe_data(missing_path)
    
    # Then: Cache returns None
    assert result is None
```

### Fixtures

#### Basic Fixtures

```python
# conftest.py
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

@pytest.fixture
def temp_dir():
    """Provide temporary directory that's cleaned up after test."""
    with TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_movie_dir(temp_dir):
    """Create sample movie directory structure."""
    movie_dir = temp_dir / "The Matrix (1999)"
    movie_dir.mkdir()
    
    # Create video file
    video_file = movie_dir / "The Matrix (1999).mkv"
    video_file.write_text("fake video content")
    
    # Create assets
    (movie_dir / "poster.jpg").write_bytes(b"fake poster image")
    (movie_dir / "fanart.jpg").write_bytes(b"fake fanart image")
    (movie_dir / "trailer.mp4").write_bytes(b"fake trailer video")
    
    return movie_dir

@pytest.fixture
def movie_parser():
    """Provide configured movie parser."""
    patterns = get_test_patterns()
    return MovieParser(patterns)
```

#### Parameterized Fixtures

```python
@pytest.fixture(params=[
    "plex",
    "jellyfin", 
    "emby",
    "all"
])
def media_server_patterns(request):
    """Provide patterns for different media servers."""
    profile = request.param
    return get_patterns([profile]).compile_patterns()

# Test will run once for each parameter
def test_parser_works_with_all_servers(movie_parser, media_server_patterns):
    parser = MovieParser(media_server_patterns)
    # Test implementation...
```

#### Scoped Fixtures

```python
# Session-scoped fixture (created once per test session)
@pytest.fixture(scope="session")
def large_test_library():
    """Create large test library (expensive operation)."""
    return create_large_test_structure()

# Module-scoped fixture (created once per test module)
@pytest.fixture(scope="module")
def database_connection():
    """Provide database connection for module tests."""
    conn = create_test_database()
    yield conn
    conn.close()

# Function-scoped fixture (default, created for each test)
@pytest.fixture(scope="function")  # or just @pytest.fixture
def clean_cache():
    """Provide clean cache for each test."""
    cache = MediaCache(enabled=True)
    yield cache
    cache.clear()
```

### Mocking and Patching

#### Using pytest-mock

```python
import pytest
from unittest.mock import MagicMock

def test_scanner_handles_ffprobe_failure(mocker):
    """Test scanner gracefully handles FFprobe failures."""
    # Mock FFprobe to raise exception
    mock_probe = mocker.patch('media_audit.probe.probe_video')
    mock_probe.side_effect = ProbeError("FFprobe not found")
    
    scanner = MediaScanner(config)
    result = scanner.scan()
    
    # Scanner should continue despite probe failure
    assert len(result.movies) > 0
    assert "FFprobe not found" in result.errors

def test_cache_hit_improves_performance(mocker):
    """Test cache hit reduces processing time."""
    # Mock cache to return cached data
    mock_cache = mocker.patch('media_audit.cache.MediaCache')
    mock_cache.get_media_item.return_value = {"name": "Cached Movie"}
    
    parser = MovieParser(patterns, cache=mock_cache)
    result = parser.parse(Path("/movies/Test Movie"))
    
    # Should use cached data without parsing
    mock_cache.get_media_item.assert_called_once()
    assert result.name == "Cached Movie"
```

#### Mocking External Dependencies

```python
@pytest.fixture
def mock_ffprobe(mocker):
    """Mock FFprobe subprocess calls."""
    mock_run = mocker.patch('subprocess.run')
    
    # Successful FFprobe response
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = json.dumps({
        "streams": [{
            "codec_type": "video",
            "codec_name": "hevc",
            "width": 1920,
            "height": 1080
        }],
        "format": {
            "duration": "7260.5",
            "bit_rate": "8500000"
        }
    })
    
    return mock_run

def test_video_info_extraction(mock_ffprobe):
    """Test video information extraction from FFprobe."""
    video_info = probe_video(Path("/test/video.mkv"))
    
    assert video_info.codec == CodecType.HEVC
    assert video_info.resolution == (1920, 1080)
    assert video_info.duration == 7260.5
    assert video_info.bitrate == 8500000
```

### Parametrized Tests

#### Basic Parametrization

```python
@pytest.mark.parametrize("directory_name,expected_title,expected_year", [
    ("The Matrix (1999)", "The Matrix", 1999),
    ("Inception (2010)", "Inception", 2010),
    ("The Lord of the Rings - The Fellowship of the Ring (2001)", 
     "The Lord of the Rings - The Fellowship of the Ring", 2001),
    ("Movie.2023.1080p.BluRay", "Movie", 2023),
])
def test_movie_title_extraction(directory_name, expected_title, expected_year):
    """Test movie title and year extraction from various formats."""
    parser = MovieParser(get_test_patterns())
    info = parser.extract_movie_info(Path(directory_name))
    
    assert info["title"] == expected_title
    assert info["year"] == expected_year
```

#### Complex Parametrization

```python
@pytest.mark.parametrize("codec,expected_status", [
    (CodecType.HEVC, ValidationStatus.VALID),
    (CodecType.AV1, ValidationStatus.VALID), 
    (CodecType.H264, ValidationStatus.WARNING),
    (CodecType.MPEG2, ValidationStatus.WARNING),
])
def test_codec_validation(codec, expected_status):
    """Test video codec validation results."""
    movie = MovieItem(
        path=Path("/test"),
        name="Test Movie",
        video_info=VideoInfo(path=Path("/test.mkv"), codec=codec)
    )
    
    validator = MediaValidator(get_test_config())
    validator.validate_movie(movie)
    
    if expected_status == ValidationStatus.VALID:
        codec_issues = [i for i in movie.issues if i.category == "encoding"]
        assert len(codec_issues) == 0
    else:
        codec_issues = [i for i in movie.issues if i.category == "encoding"]
        assert len(codec_issues) > 0
        assert codec_issues[0].severity == expected_status
```

### Property-Based Testing

Use [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing:

```python
from hypothesis import given, strategies as st
import pytest

@given(st.text(min_size=1, max_size=100))
def test_movie_name_handling(movie_name):
    """Test movie parser handles arbitrary movie names."""
    # Assume movie names don't contain path separators
    assume('/' not in movie_name and '\\' not in movie_name)
    
    movie = MovieItem(path=Path("/movies") / movie_name, name=movie_name)
    
    # Property: movie name should always be preserved
    assert movie.name == movie_name
    assert len(movie.name) > 0

@given(st.integers(min_value=1900, max_value=2100))
def test_movie_year_validation(year):
    """Test movie year validation with generated years."""
    movie = MovieItem(
        path=Path("/test"),
        name="Test Movie", 
        year=year
    )
    
    # Property: valid years should be preserved
    assert movie.year == year
    assert 1900 <= movie.year <= 2100
```

## Integration Testing

### Testing Component Interactions

```python
class TestScannerIntegration:
    """Integration tests for media scanner."""
    
    def test_complete_movie_scanning_workflow(self, temp_dir):
        """Test complete movie scanning from directory to results."""
        # Arrange: Create realistic test directory structure
        movies_dir = temp_dir / "Movies"
        movies_dir.mkdir()
        
        # Create multiple movies with various asset combinations
        self.create_movie_with_all_assets(movies_dir / "Complete Movie (2020)")
        self.create_movie_missing_poster(movies_dir / "Missing Poster (2021)")
        self.create_movie_h264_codec(movies_dir / "Old Codec (2019)")
        
        # Configure scanner
        config = ScanConfig(
            root_paths=[temp_dir],
            allowed_codecs=[CodecType.HEVC, CodecType.AV1],
            concurrent_workers=1  # Single-threaded for predictable tests
        )
        scanner = MediaScanner(config)
        
        # Act: Run complete scan
        result = scanner.scan()
        
        # Assert: Verify scan results
        assert len(result.movies) == 3
        assert result.total_items == 3
        assert result.total_issues > 0  # Should find some issues
        
        # Check specific movie results
        complete_movie = next(m for m in result.movies if "Complete" in m.name)
        assert len(complete_movie.issues) == 0
        
        missing_poster_movie = next(m for m in result.movies if "Missing" in m.name)
        assert any(i.category == "assets" for i in missing_poster_movie.issues)
        
        old_codec_movie = next(m for m in result.movies if "Old" in m.name)
        assert any(i.category == "encoding" for i in old_codec_movie.issues)
    
    def test_tv_show_hierarchical_scanning(self, temp_dir):
        """Test TV show scanning with nested season/episode structure."""
        # Create complex TV show structure
        series_dir = self.create_complete_tv_series(temp_dir)
        
        config = ScanConfig(root_paths=[temp_dir])
        scanner = MediaScanner(config)
        
        result = scanner.scan()
        
        assert len(result.series) == 1
        series = result.series[0]
        assert len(series.seasons) == 2
        assert series.total_episodes == 4
        
        # Verify hierarchical validation worked
        assert series.status in [ValidationStatus.VALID, ValidationStatus.WARNING]
        for season in series.seasons:
            assert len(season.episodes) == 2
            for episode in season.episodes:
                assert episode.type == MediaType.TV_EPISODE
```

### Testing External Integrations

```python
class TestFFprobeIntegration:
    """Integration tests for FFprobe functionality."""
    
    def test_ffprobe_with_real_video_file(self, sample_video_file):
        """Test FFprobe analysis with actual video file."""
        # This test requires actual video files
        if not sample_video_file.exists():
            pytest.skip("Sample video file not available")
        
        video_info = probe_video(sample_video_file)
        
        assert video_info is not None
        assert video_info.codec is not None
        assert video_info.resolution is not None
        assert video_info.duration > 0
        assert video_info.size > 0
    
    @pytest.mark.skipif(not shutil.which("ffprobe"), reason="FFprobe not available")
    def test_ffprobe_error_handling(self, temp_dir):
        """Test FFprobe error handling with invalid files."""
        # Create invalid video file
        invalid_file = temp_dir / "invalid.mkv"
        invalid_file.write_text("This is not a video file")
        
        with pytest.raises(ProbeError):
            probe_video(invalid_file)
```

## End-to-End Testing

### CLI Testing

```python
from click.testing import CliRunner
from media_audit.cli import cli

class TestCLIEndToEnd:
    """End-to-end tests for CLI functionality."""
    
    def test_scan_command_with_html_output(self, temp_dir):
        """Test complete scan command producing HTML report."""
        # Arrange: Create test media structure
        self.create_test_media_library(temp_dir)
        
        report_path = temp_dir / "test-report.html"
        
        # Act: Run CLI command
        runner = CliRunner()
        result = runner.invoke(cli, [
            'scan',
            '--roots', str(temp_dir),
            '--report', str(report_path),
            '--workers', '1'
        ])
        
        # Assert: Command succeeded and report was created
        assert result.exit_code == 0
        assert report_path.exists()
        assert "Media Audit Scanner" in result.output
        
        # Verify report content
        report_content = report_path.read_text()
        assert "<html>" in report_content
        assert "Scan Summary" in report_content
    
    def test_scan_command_problems_only(self, temp_dir):
        """Test scan command with problems-only flag."""
        # Create media with known issues
        self.create_media_with_issues(temp_dir)
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'scan',
            '--roots', str(temp_dir),
            '--problems-only',
            '--json', str(temp_dir / "issues.json")
        ])
        
        assert result.exit_code == 1  # Issues found
        assert "issues found" in result.output.lower()
        
        # Verify JSON contains only items with issues
        json_data = json.loads((temp_dir / "issues.json").read_text())
        movies_with_issues = [m for m in json_data["movies"] if m["issues"]]
        assert len(movies_with_issues) > 0
```

### Performance Testing

```python
@pytest.mark.slow
class TestPerformance:
    """Performance and scalability tests."""
    
    def test_large_library_performance(self, large_test_library):
        """Test performance with large media library."""
        # Test with 1000+ items
        config = ScanConfig(
            root_paths=[large_test_library],
            concurrent_workers=4,
            cache_enabled=True
        )
        scanner = MediaScanner(config)
        
        start_time = time.time()
        result = scanner.scan()
        end_time = time.time()
        
        scan_duration = end_time - start_time
        
        # Performance assertions
        assert result.total_items >= 1000
        assert scan_duration < 300  # Should complete within 5 minutes
        assert scan_duration / result.total_items < 0.1  # < 0.1 seconds per item
    
    @pytest.mark.benchmark
    def test_cache_performance_improvement(self, benchmark, sample_movie_dir):
        """Benchmark cache performance improvement."""
        parser = MovieParser(get_test_patterns(), cache=MediaCache(enabled=True))
        
        def parse_movie():
            return parser.parse(sample_movie_dir)
        
        # First run (no cache)
        result1 = benchmark.pedantic(parse_movie, rounds=1, iterations=1)
        
        # Second run (with cache) - should be faster
        result2 = benchmark(parse_movie)
        
        assert result1.name == result2.name  # Same result
        # Cache run should be significantly faster
```

## Test Configuration

### pytest.ini

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --strict-config
    --disable-warnings
    --tb=short
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    benchmark: marks tests as benchmarks
    requires_ffprobe: requires FFprobe to be installed
    requires_sample_media: requires sample media files
filterwarnings =
    error
    ignore::UserWarning
    ignore::DeprecationWarning
```

### Test Markers

```python
import pytest

# Mark slow tests
@pytest.mark.slow
def test_large_library_processing():
    pass

# Mark tests requiring external dependencies
@pytest.mark.requires_ffprobe
def test_video_analysis():
    pass

# Mark integration tests
@pytest.mark.integration
def test_scanner_with_validator():
    pass

# Custom markers for test organization
@pytest.mark.parser
@pytest.mark.unit
def test_movie_parser_validation():
    pass
```

## Test Data Management

### Fixture Data

```python
# tests/fixtures/sample_data.py
from pathlib import Path

def create_sample_movie_structure(base_path: Path, movie_name: str = "Sample Movie (2020)"):
    """Create standardized movie test structure."""
    movie_dir = base_path / movie_name
    movie_dir.mkdir(parents=True, exist_ok=True)
    
    # Create video file
    video_file = movie_dir / f"{movie_name}.mkv"
    video_file.write_bytes(b"fake video content")
    
    # Create standard assets
    (movie_dir / "poster.jpg").write_bytes(create_fake_image())
    (movie_dir / "fanart.jpg").write_bytes(create_fake_image())
    (movie_dir / "trailer.mp4").write_bytes(b"fake trailer")
    
    return movie_dir

def create_fake_image() -> bytes:
    """Create minimal fake image data."""
    # Minimal PNG header
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\r\n\xa7\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
```

### Environment Setup for Tests

```python
# conftest.py
import os
import tempfile
import pytest
from pathlib import Path

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Ensure tests don't interfere with user's cache
    test_cache_dir = tempfile.mkdtemp(prefix="media-audit-test-")
    os.environ["MEDIA_AUDIT_CACHE_DIR"] = test_cache_dir
    
    # Disable real FFprobe calls in most tests
    os.environ["MEDIA_AUDIT_MOCK_FFPROBE"] = "1"
    
    yield
    
    # Cleanup
    import shutil
    shutil.rmtree(test_cache_dir, ignore_errors=True)
```

## Continuous Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.13']

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install FFmpeg
      uses: FedericoCarboni/setup-ffmpeg@v2
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install uv
        uv pip install -e ".[dev,test]"
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml --cov-report=term-missing
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

## Best Practices

### Test Quality Guidelines

1. **Test Behavior, Not Implementation**: Test what the code does, not how it does it
2. **Clear Test Names**: Use descriptive names that explain what is being tested
3. **Single Responsibility**: Each test should verify one specific behavior
4. **Deterministic**: Tests should produce consistent results
5. **Independent**: Tests should not depend on other tests
6. **Fast**: Unit tests should run quickly
7. **Maintainable**: Tests should be easy to understand and modify

### Common Anti-Patterns to Avoid

```python
# Avoid: Testing implementation details
def test_parser_calls_extract_metadata_method():
    # This tests implementation, not behavior
    pass

# Better: Test the behavior/outcome
def test_parser_extracts_movie_year_from_directory_name():
    parser = MovieParser()
    result = parser.parse(Path("Movie (2020)"))
    assert result.year == 2020

# Avoid: Over-mocking
def test_scanner_with_everything_mocked(mocker):
    mocker.patch('every.single.dependency')
    # This test doesn't verify real behavior
    pass

# Better: Mock only external dependencies
def test_scanner_handles_ffprobe_failure(mocker):
    mocker.patch('subprocess.run', side_effect=OSError("FFprobe failed"))
    # Test real behavior with mocked external call
    pass
```

### Testing Checklist

Before submitting code:

- [ ] All tests pass locally
- [ ] New features have corresponding tests  
- [ ] Edge cases are covered
- [ ] Error conditions are tested
- [ ] Tests are deterministic and independent
- [ ] Test names are descriptive
- [ ] No test anti-patterns are present
- [ ] Coverage is maintained or improved

This comprehensive testing guide ensures Media Audit maintains high code quality and reliability through effective testing practices.