#!/usr/bin/env python3
"""
Metrics collection module.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging

from pefc.metrics.types import MetricsData, MetricsRun
from pefc.metrics.validator import validate_metrics_data

log = logging.getLogger(__name__)


class MetricsCollector:
    """Collects metrics from various sources."""

    def __init__(self, sources: List[str], schema_path: Optional[str] = None):
        """Initialize metrics collector.

        Args:
            sources: List of source paths to collect metrics from
            schema_path: Optional path to JSON schema for validation
        """
        self.sources = sources
        self.schema_path = schema_path
        self.collected_metrics: List[MetricsRun] = []

    def collect(self) -> MetricsData:
        """Collect metrics from all sources.

        Returns:
            Collected metrics data
        """
        log.info("Starting metrics collection from %d sources", len(self.sources))

        for source in self.sources:
            try:
                metrics_run = self._collect_from_source(source)
                if metrics_run:
                    self.collected_metrics.append(metrics_run)
                    log.info("Collected metrics from %s", source)
                else:
                    log.warning("No metrics found in %s", source)
            except Exception as e:
                log.error("Failed to collect metrics from %s: %s", source, e)
                continue

        log.info("Collected %d metrics runs", len(self.collected_metrics))

        # Create metrics data
        metrics_data = MetricsData(
            runs=self.collected_metrics,
            total_runs=len(self.collected_metrics),
            collection_timestamp=self._get_timestamp(),
        )

        # Validate if schema is provided
        if self.schema_path:
            try:
                validate_metrics_data(metrics_data, Path(self.schema_path))
                log.info("Metrics data validated against schema")
            except Exception as e:
                log.warning("Metrics validation failed: %s", e)

        return metrics_data

    def _collect_from_source(self, source: str) -> Optional[MetricsRun]:
        """Collect metrics from a single source.

        Args:
            source: Source path

        Returns:
            Metrics run or None if collection failed
        """
        source_path = Path(source)

        if not source_path.exists():
            log.warning("Source path does not exist: %s", source)
            return None

        if source_path.is_file():
            return self._collect_from_file(source_path)
        elif source_path.is_dir():
            return self._collect_from_directory(source_path)
        else:
            log.warning("Unknown source type: %s", source)
            return None

    def _collect_from_file(self, file_path: Path) -> Optional[MetricsRun]:
        """Collect metrics from a single file.

        Args:
            file_path: Path to metrics file

        Returns:
            Metrics run or None if collection failed
        """
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Extract metrics from file
            metrics = data.get("metrics", {})
            run_id = data.get("run_id", file_path.stem)
            timestamp = data.get("timestamp", self._get_timestamp())

            return MetricsRun(run_id=run_id, timestamp=timestamp, metrics=metrics)
        except Exception as e:
            log.error("Failed to collect metrics from file %s: %s", file_path, e)
            return None

    def _collect_from_directory(self, dir_path: Path) -> Optional[MetricsRun]:
        """Collect metrics from a directory.

        Args:
            dir_path: Path to metrics directory

        Returns:
            Metrics run or None if collection failed
        """
        # Look for metrics files in directory
        metrics_files = list(dir_path.glob("*.json"))

        if not metrics_files:
            log.warning("No JSON files found in directory: %s", dir_path)
            return None

        # Use the first file found
        return self._collect_from_file(metrics_files[0])

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"

    def save_collected_metrics(self, output_path: Path) -> None:
        """Save collected metrics to file.

        Args:
            output_path: Path to save metrics to
        """
        try:
            with open(output_path, "w") as f:
                json.dump(self.collected_metrics, f, indent=2)
            log.info("Saved collected metrics to %s", output_path)
        except Exception as e:
            log.error("Failed to save collected metrics: %s", e)
            raise

    def get_collected_metrics(self) -> List[MetricsRun]:
        """Get collected metrics.

        Returns:
            List of collected metrics runs
        """
        return self.collected_metrics

    def clear_collected_metrics(self) -> None:
        """Clear collected metrics."""
        self.collected_metrics.clear()
        log.info("Cleared collected metrics")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics.

        Returns:
            Summary of collected metrics
        """
        if not self.collected_metrics:
            return {"total_runs": 0, "metrics": {}}

        # Calculate summary statistics
        total_runs = len(self.collected_metrics)
        all_metrics = {}

        for run in self.collected_metrics:
            for metric_name, metric_value in run.metrics.items():
                if metric_name not in all_metrics:
                    all_metrics[metric_name] = []
                all_metrics[metric_name].append(metric_value)

        # Calculate statistics for each metric
        summary_metrics = {}
        for metric_name, values in all_metrics.items():
            if values:
                summary_metrics[metric_name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                }

        return {"total_runs": total_runs, "metrics": summary_metrics}
