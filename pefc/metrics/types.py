#!/usr/bin/env python3
"""
Metrics types module.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class RunRecord:
    """Represents a single metrics run record."""

    run_id: str
    group: str
    weight: float
    metrics: Dict[str, float]
    source_path: str

    def __post_init__(self):
        """Validate run record after initialization."""
        if not self.run_id:
            raise ValueError("run_id cannot be empty")
        if not self.group:
            raise ValueError("group cannot be empty")
        if not isinstance(self.weight, (int, float)):
            raise ValueError("weight must be a number")
        if self.weight < 0:
            raise ValueError("weight must be non-negative")
        if not isinstance(self.metrics, dict):
            raise ValueError("metrics must be a dictionary")
        if not self.source_path:
            raise ValueError("source_path cannot be empty")

        # Validate metric values
        for metric_name, metric_value in self.metrics.items():
            if not isinstance(metric_value, (int, float)):
                raise ValueError(f"Metric {metric_name} must be a number")
            if metric_value < 0:
                raise ValueError(f"Metric {metric_name} must be non-negative")

    def get_metric(self, metric_name: str) -> Optional[float]:
        """Get a specific metric value.

        Args:
            metric_name: Name of the metric

        Returns:
            Metric value or None if not found
        """
        return self.metrics.get(metric_name)

    def set_metric(self, metric_name: str, metric_value: float) -> None:
        """Set a metric value.

        Args:
            metric_name: Name of the metric
            metric_value: Value of the metric
        """
        if not isinstance(metric_value, (int, float)):
            raise ValueError("Metric value must be a number")
        if metric_value < 0:
            raise ValueError("Metric value must be non-negative")

        self.metrics[metric_name] = float(metric_value)

    def has_metric(self, metric_name: str) -> bool:
        """Check if a metric exists.

        Args:
            metric_name: Name of the metric

        Returns:
            True if metric exists, False otherwise
        """
        return metric_name in self.metrics

    def get_metrics_count(self) -> int:
        """Get number of metrics.

        Returns:
            Number of metrics
        """
        return len(self.metrics)

    def get_metrics_names(self) -> List[str]:
        """Get names of all metrics.

        Returns:
            List of metric names
        """
        return list(self.metrics.keys())

    def get_metrics_values(self) -> List[float]:
        """Get values of all metrics.

        Returns:
            List of metric values
        """
        return list(self.metrics.values())

    def get_metrics_sum(self) -> float:
        """Get sum of all metrics.

        Returns:
            Sum of all metrics
        """
        return sum(self.metrics.values())

    def get_metrics_avg(self) -> float:
        """Get average of all metrics.

        Returns:
            Average of all metrics
        """
        if not self.metrics:
            return 0.0
        return sum(self.metrics.values()) / len(self.metrics)

    def get_metrics_min(self) -> float:
        """Get minimum of all metrics.

        Returns:
            Minimum of all metrics
        """
        if not self.metrics:
            return 0.0
        return min(self.metrics.values())

    def get_metrics_max(self) -> float:
        """Get maximum of all metrics.

        Returns:
            Maximum of all metrics
        """
        if not self.metrics:
            return 0.0
        return max(self.metrics.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "run_id": self.run_id,
            "group": self.group,
            "weight": self.weight,
            "metrics": self.metrics,
            "source_path": self.source_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RunRecord:
        """Create from dictionary.

        Args:
            data: Dictionary data

        Returns:
            RunRecord instance
        """
        return cls(
            run_id=data["run_id"],
            group=data["group"],
            weight=data["weight"],
            metrics=data["metrics"],
            source_path=data["source_path"],
        )


@dataclass
class MetricsRun:
    """Represents a single metrics run."""

    run_id: str
    timestamp: str
    metrics: Dict[str, float]

    def __post_init__(self):
        """Validate metrics run after initialization."""
        if not self.run_id:
            raise ValueError("run_id cannot be empty")
        if not self.timestamp:
            raise ValueError("timestamp cannot be empty")
        if not isinstance(self.metrics, dict):
            raise ValueError("metrics must be a dictionary")

        # Validate metric values
        for metric_name, metric_value in self.metrics.items():
            if not isinstance(metric_value, (int, float)):
                raise ValueError(f"Metric {metric_name} must be a number")
            if metric_value < 0:
                raise ValueError(f"Metric {metric_name} must be non-negative")

    def get_metric(self, metric_name: str) -> Optional[float]:
        """Get a specific metric value.

        Args:
            metric_name: Name of the metric

        Returns:
            Metric value or None if not found
        """
        return self.metrics.get(metric_name)

    def set_metric(self, metric_name: str, metric_value: float) -> None:
        """Set a metric value.

        Args:
            metric_name: Name of the metric
            metric_value: Value of the metric
        """
        if not isinstance(metric_value, (int, float)):
            raise ValueError("Metric value must be a number")
        if metric_value < 0:
            raise ValueError("Metric value must be non-negative")

        self.metrics[metric_name] = float(metric_value)

    def has_metric(self, metric_name: str) -> bool:
        """Check if a metric exists.

        Args:
            metric_name: Name of the metric

        Returns:
            True if metric exists, False otherwise
        """
        return metric_name in self.metrics

    def get_metrics_count(self) -> int:
        """Get number of metrics.

        Returns:
            Number of metrics
        """
        return len(self.metrics)

    def get_metrics_names(self) -> List[str]:
        """Get names of all metrics.

        Returns:
            List of metric names
        """
        return list(self.metrics.keys())

    def get_metrics_values(self) -> List[float]:
        """Get values of all metrics.

        Returns:
            List of metric values
        """
        return list(self.metrics.values())

    def get_metrics_sum(self) -> float:
        """Get sum of all metrics.

        Returns:
            Sum of all metrics
        """
        return sum(self.metrics.values())

    def get_metrics_avg(self) -> float:
        """Get average of all metrics.

        Returns:
            Average of all metrics
        """
        if not self.metrics:
            return 0.0
        return sum(self.metrics.values()) / len(self.metrics)

    def get_metrics_min(self) -> float:
        """Get minimum of all metrics.

        Returns:
            Minimum of all metrics
        """
        if not self.metrics:
            return 0.0
        return min(self.metrics.values())

    def get_metrics_max(self) -> float:
        """Get maximum of all metrics.

        Returns:
            Maximum of all metrics
        """
        if not self.metrics:
            return 0.0
        return max(self.metrics.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MetricsRun:
        """Create from dictionary.

        Args:
            data: Dictionary data

        Returns:
            MetricsRun instance
        """
        return cls(run_id=data["run_id"], timestamp=data["timestamp"], metrics=data["metrics"])


@dataclass
class MetricsData:
    """Represents collected metrics data."""

    runs: List[MetricsRun]
    total_runs: int
    collection_timestamp: str

    def __post_init__(self):
        """Validate metrics data after initialization."""
        if not isinstance(self.runs, list):
            raise ValueError("runs must be a list")
        if self.total_runs != len(self.runs):
            raise ValueError("total_runs must match length of runs")
        if not self.collection_timestamp:
            raise ValueError("collection_timestamp cannot be empty")

        # Validate all runs
        for run in self.runs:
            if not isinstance(run, MetricsRun):
                raise ValueError("All runs must be MetricsRun instances")

    def get_run(self, run_id: str) -> Optional[MetricsRun]:
        """Get a specific run by ID.

        Args:
            run_id: ID of the run

        Returns:
            MetricsRun or None if not found
        """
        for run in self.runs:
            if run.run_id == run_id:
                return run
        return None

    def get_runs_by_metric(self, metric_name: str) -> List[MetricsRun]:
        """Get runs that have a specific metric.

        Args:
            metric_name: Name of the metric

        Returns:
            List of runs with the metric
        """
        return [run for run in self.runs if run.has_metric(metric_name)]

    def get_metric_values(self, metric_name: str) -> List[float]:
        """Get values of a specific metric across all runs.

        Args:
            metric_name: Name of the metric

        Returns:
            List of metric values
        """
        values = []
        for run in self.runs:
            if run.has_metric(metric_name):
                values.append(run.get_metric(metric_name))
        return values

    def get_metric_summary(self, metric_name: str) -> Dict[str, float]:
        """Get summary of a specific metric.

        Args:
            metric_name: Name of the metric

        Returns:
            Summary of the metric
        """
        values = self.get_metric_values(metric_name)
        if not values:
            return {"count": 0, "sum": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0}

        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }

    def get_all_metrics_names(self) -> List[str]:
        """Get names of all metrics across all runs.

        Returns:
            List of metric names
        """
        metric_names = set()
        for run in self.runs:
            metric_names.update(run.get_metrics_names())
        return sorted(metric_names)

    def get_total_metrics_count(self) -> int:
        """Get total number of metrics across all runs.

        Returns:
            Total number of metrics
        """
        return sum(run.get_metrics_count() for run in self.runs)

    def get_metrics_density(self) -> float:
        """Get metrics density (average metrics per run).

        Returns:
            Metrics density
        """
        if not self.runs:
            return 0.0
        return self.get_total_metrics_count() / len(self.runs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "runs": [run.to_dict() for run in self.runs],
            "total_runs": self.total_runs,
            "collection_timestamp": self.collection_timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MetricsData:
        """Create from dictionary.

        Args:
            data: Dictionary data

        Returns:
            MetricsData instance
        """
        runs = [MetricsRun.from_dict(run_data) for run_data in data["runs"]]
        return cls(
            runs=runs,
            total_runs=data["total_runs"],
            collection_timestamp=data["collection_timestamp"],
        )
