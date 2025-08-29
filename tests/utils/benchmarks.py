"""
Performance benchmarking utilities for tests.
"""

import functools
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""

    name: str
    runs: int
    times: list[float] = field(default_factory=list)

    @property
    def min_time(self) -> float:
        return min(self.times) if self.times else 0

    @property
    def max_time(self) -> float:
        return max(self.times) if self.times else 0

    @property
    def mean_time(self) -> float:
        return statistics.mean(self.times) if self.times else 0

    @property
    def median_time(self) -> float:
        return statistics.median(self.times) if self.times else 0

    @property
    def stddev(self) -> float:
        return statistics.stdev(self.times) if len(self.times) > 1 else 0

    def assert_faster_than(self, seconds: float):
        """Assert benchmark is faster than threshold."""
        assert self.mean_time < seconds, (
            f"{self.name} mean time {self.mean_time:.3f}s exceeds threshold {seconds}s"
        )

    def summary(self) -> str:
        """Get benchmark summary."""
        return (
            f"{self.name}: {self.runs} runs\n"
            f"  Min: {self.min_time:.3f}s\n"
            f"  Max: {self.max_time:.3f}s\n"
            f"  Mean: {self.mean_time:.3f}s\n"
            f"  Median: {self.median_time:.3f}s\n"
            f"  StdDev: {self.stddev:.3f}s"
        )


class Benchmark:
    """Simple benchmarking utility."""

    def __init__(self, name: str = "Benchmark"):
        self.name = name
        self.results: list[BenchmarkResult] = []

    def run(
        self, func: Callable, runs: int = 10, warmup: int = 2, name: str = None
    ) -> BenchmarkResult:
        """Run a benchmark."""
        name = name or func.__name__

        # Warmup runs
        for _ in range(warmup):
            func()

        # Benchmark runs
        times = []
        for _ in range(runs):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append(end - start)

        result = BenchmarkResult(name=name, runs=runs, times=times)
        self.results.append(result)
        return result

    def compare(self, baseline: str, candidate: str) -> float:
        """Compare two benchmark results."""
        baseline_result = next((r for r in self.results if r.name == baseline), None)
        candidate_result = next((r for r in self.results if r.name == candidate), None)

        if not baseline_result or not candidate_result:
            raise ValueError("Both benchmarks must be run first")

        speedup = baseline_result.mean_time / candidate_result.mean_time
        return speedup

    def report(self) -> str:
        """Generate benchmark report."""
        lines = [f"Benchmark Report: {self.name}", "=" * 50]

        for result in self.results:
            lines.append(result.summary())
            lines.append("")

        return "\n".join(lines)


def benchmark_decorator(runs: int = 10, warmup: int = 2):
    """Decorator to benchmark a function."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bench = Benchmark(func.__name__)

            def run_func():
                return func(*args, **kwargs)

            result = bench.run(run_func, runs=runs, warmup=warmup)
            print(f"\n{result.summary()}")

            # Run the actual function once and return result
            return func(*args, **kwargs)

        return wrapper

    return decorator


class MemoryTracker:
    """Track memory usage in tests."""

    def __init__(self):
        self.initial_memory = None
        self.peak_memory = None
        self.final_memory = None

    def start(self):
        """Start tracking memory."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        self.initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    def check(self) -> float:
        """Check current memory usage."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        current = process.memory_info().rss / 1024 / 1024  # MB

        if self.peak_memory is None or current > self.peak_memory:
            self.peak_memory = current

        return current

    def stop(self) -> dict:
        """Stop tracking and return stats."""
        self.final_memory = self.check()

        return {
            "initial_mb": self.initial_memory,
            "final_mb": self.final_memory,
            "peak_mb": self.peak_memory,
            "growth_mb": self.final_memory - self.initial_memory,
        }

    def assert_memory_limit(self, limit_mb: float):
        """Assert memory usage stays under limit."""
        current = self.check()
        assert current < limit_mb, f"Memory usage {current:.1f}MB exceeds limit {limit_mb}MB"


class LoadTest:
    """Simple load testing utility."""

    @staticmethod
    async def concurrent_load(func: Callable, concurrency: int = 10, duration: float = 1.0) -> dict:
        """Run concurrent load test."""
        import asyncio

        start_time = time.time()
        end_time = start_time + duration

        completed = 0
        errors = 0

        async def worker():
            nonlocal completed, errors

            while time.time() < end_time:
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func()
                    else:
                        func()
                    completed += 1
                except Exception:
                    errors += 1

        workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
        await asyncio.gather(*workers)

        actual_duration = time.time() - start_time

        return {
            "completed": completed,
            "errors": errors,
            "duration": actual_duration,
            "throughput": completed / actual_duration,
            "error_rate": errors / (completed + errors) if (completed + errors) > 0 else 0,
        }

    @staticmethod
    def ramp_load(
        func: Callable,
        start_concurrency: int = 1,
        max_concurrency: int = 10,
        step: int = 1,
        step_duration: float = 1.0,
    ) -> list[dict]:
        """Run ramping load test."""
        results = []

        for concurrency in range(start_concurrency, max_concurrency + 1, step):
            print(f"Testing with {concurrency} concurrent workers...")

            import asyncio

            result = asyncio.run(LoadTest.concurrent_load(func, concurrency, step_duration))
            result["concurrency"] = concurrency
            results.append(result)

            # Stop if error rate is too high
            if result["error_rate"] > 0.1:
                print(f"Stopping due to high error rate: {result['error_rate']:.1%}")
                break

        return results
