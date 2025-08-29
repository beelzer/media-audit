"""
Test utilities and helpers.
"""

from .assertions import (
    MediaAssetsAssertions,
    PathAssertions,
    ValidationIssueAssertions,
    ValueAssertions,
    VideoInfoAssertions,
    assert_async_result,
    assert_no_exceptions,
)
from .base import (
    AsyncTestHelper,
    DataGenerator,
    FlexibleMock,
    TestContext,
    TestDataBuilder,
    assert_eventually,
    isolated_test_env,
)
from .benchmarks import (
    Benchmark,
    BenchmarkResult,
    LoadTest,
    MemoryTracker,
    benchmark_decorator,
)
from .factories import (
    ConfigFactory,
    FFProbeDataFactory,
    MediaAssetsFactory,
    ValidationIssueFactory,
    VideoInfoFactory,
)
from .fixtures import (
    MediaFileBuilder,
    PerformanceTimer,
    TestDataManager,
    TestDataSet,
    parametrize_with_ids,
    temp_media_library,
)
from .helpers import (
    AsyncTestRunner,
    ExceptionContext,
    PatchManager,
    TempEnvironment,
    capture_logs,
    create_mock_with_spec,
    mock_async_iter,
    retry_test,
    skip_on_ci,
    skip_on_windows,
    wait_for_condition,
)
from .mocks import (
    MockCache,
    MockFFProbe,
    MockFileSystem,
    MockLogger,
    MockProgressBar,
    create_async_context_manager,
    create_mock_scanner,
)

__all__ = [
    # Assertions
    "VideoInfoAssertions",
    "ValidationIssueAssertions",
    "MediaAssetsAssertions",
    "PathAssertions",
    "ValueAssertions",
    "assert_async_result",
    "assert_no_exceptions",
    # Base utilities
    "AsyncTestHelper",
    "DataGenerator",
    "FlexibleMock",
    "TestContext",
    "TestDataBuilder",
    "assert_eventually",
    "isolated_test_env",
    # Benchmarks
    "Benchmark",
    "BenchmarkResult",
    "benchmark_decorator",
    "LoadTest",
    "MemoryTracker",
    # Factories
    "ConfigFactory",
    "FFProbeDataFactory",
    "VideoInfoFactory",
    "MediaAssetsFactory",
    "ValidationIssueFactory",
    # Fixtures
    "MediaFileBuilder",
    "PerformanceTimer",
    "TestDataManager",
    "TestDataSet",
    "parametrize_with_ids",
    "temp_media_library",
    # Helpers
    "AsyncTestRunner",
    "ExceptionContext",
    "PatchManager",
    "TempEnvironment",
    "capture_logs",
    "create_mock_with_spec",
    "mock_async_iter",
    "retry_test",
    "skip_on_ci",
    "skip_on_windows",
    "wait_for_condition",
    # Mocks
    "MockCache",
    "MockFFProbe",
    "MockFileSystem",
    "MockLogger",
    "MockProgressBar",
    "create_async_context_manager",
    "create_mock_scanner",
]
