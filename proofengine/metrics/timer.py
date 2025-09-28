"""
Timer utilities for real performance measurement.
"""

from time import perf_counter
from contextlib import contextmanager
from typing import Generator


@contextmanager
def span() -> Generator[float, None, None]:
    """Context manager for timing operations."""
    t0 = perf_counter()
    try:
        yield t0
    finally:
        pass


def elapsed_ms(t0: float, t1: float) -> float:
    """Calculate elapsed time in milliseconds."""
    return (t1 - t0) * 1000.0


def measure_time(func):
    """Decorator to measure function execution time."""

    def wrapper(*args, **kwargs):
        start = perf_counter()
        result = func(*args, **kwargs)
        end = perf_counter()
        duration_ms = elapsed_ms(start, end)
        return result, duration_ms

    return wrapper
