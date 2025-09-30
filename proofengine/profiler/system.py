"""
System profiler for 2-category transformations.
Provides lightweight profiling and performance analysis.
"""

import time
import cProfile
import pstats
import io
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from contextlib import contextmanager
from pathlib import Path


@dataclass
class ProfileEntry:
    """Profile entry for a specific operation."""

    name: str
    start_time: float
    end_time: float
    duration: float
    memory_mb: float = 0.0
    cpu_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "memory_mb": self.memory_mb,
            "cpu_percent": self.cpu_percent,
        }


class SystemProfiler:
    """Lightweight system profiler."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.entries: List[ProfileEntry] = []
        self._active_spans: Dict[str, float] = {}
        self._cprofile = None
        self._stats = None

    def start_span(self, name: str) -> None:
        """Start profiling a span."""
        if not self.enabled:
            return

        self._active_spans[name] = time.perf_counter()

    def end_span(self, name: str) -> Optional[ProfileEntry]:
        """End profiling a span."""
        if not self.enabled or name not in self._active_spans:
            return None

        start_time = self._active_spans.pop(name)
        end_time = time.perf_counter()
        duration = end_time - start_time

        entry = ProfileEntry(name=name, start_time=start_time, end_time=end_time, duration=duration)

        self.entries.append(entry)
        return entry

    @contextmanager
    def span(self, name: str):
        """Context manager for profiling spans."""
        self.start_span(name)
        try:
            yield
        finally:
            self.end_span(name)

    def start_cprofile(self) -> None:
        """Start cProfile profiling."""
        if not self.enabled:
            return

        self._cprofile = cProfile.Profile()
        self._cprofile.enable()

    def stop_cprofile(self) -> None:
        """Stop cProfile profiling."""
        if not self.enabled or not self._cprofile:
            return

        self._cprofile.disable()
        self._stats = pstats.Stats(self._cprofile)

    def get_cprofile_stats(self) -> Optional[str]:
        """Get cProfile statistics as string."""
        if not self._stats:
            return None

        s = io.StringIO()
        self._stats.print_stats(sort="cumulative", stream=s)
        return s.getvalue()

    def get_hot_spots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get hottest code paths."""
        if not self._stats:
            return []

        hot_spots = []
        for func, (cc, nc, tt, ct, callers) in self._stats.stats.items():
            hot_spots.append(
                {
                    "function": f"{func[0]}:{func[1]}({func[2]})",
                    "cumulative_time": ct,
                    "total_time": tt,
                    "calls": cc,
                    "calls_per_second": cc / ct if ct > 0 else 0,
                }
            )

        return sorted(hot_spots, key=lambda x: x["cumulative_time"], reverse=True)[:limit]

    def get_span_summary(self) -> Dict[str, Any]:
        """Get summary of all spans."""
        if not self.entries:
            return {}

        total_duration = sum(entry.duration for entry in self.entries)
        span_counts = {}
        span_totals = {}

        for entry in self.entries:
            if entry.name not in span_counts:
                span_counts[entry.name] = 0
                span_totals[entry.name] = 0.0

            span_counts[entry.name] += 1
            span_totals[entry.name] += entry.duration

        summary = {
            "total_spans": len(self.entries),
            "total_duration": total_duration,
            "span_breakdown": {},
        }

        for name in span_counts:
            summary["span_breakdown"][name] = {
                "count": span_counts[name],
                "total_duration": span_totals[name],
                "avg_duration": span_totals[name] / span_counts[name],
                "percentage": (
                    (span_totals[name] / total_duration * 100) if total_duration > 0 else 0
                ),
            }

        return summary

    def save_profile(self, output_path: str) -> None:
        """Save profile data to file."""
        if not self.enabled:
            return

        profile_data = {
            "spans": [entry.to_dict() for entry in self.entries],
            "summary": self.get_span_summary(),
            "hot_spots": self.get_hot_spots(),
            "cprofile_stats": self.get_cprofile_stats(),
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(str(profile_data))

    def clear(self) -> None:
        """Clear all profile data."""
        self.entries.clear()
        self._active_spans.clear()
        self._cprofile = None
        self._stats = None


# Global profiler instance
system_profiler = SystemProfiler()


def profile_span(name: str):
    """Decorator for profiling function spans."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with system_profiler.span(name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def start_profiling() -> None:
    """Start system profiling."""
    system_profiler.start_cprofile()


def stop_profiling() -> None:
    """Stop system profiling."""
    system_profiler.stop_cprofile()


def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report."""
    return {
        "span_summary": system_profiler.get_span_summary(),
        "hot_spots": system_profiler.get_hot_spots(),
        "cprofile_stats": system_profiler.get_cprofile_stats(),
    }
