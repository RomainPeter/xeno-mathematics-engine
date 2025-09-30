#!/usr/bin/env python3
"""
Metrics summary module.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging

from pefc.metrics.types import MetricsData
from pefc.metrics.validator import validate_metrics_data

log = logging.getLogger(__name__)


class SummaryBuilder:
    """Builds summary from metrics data."""

    def __init__(self, metrics_data: MetricsData, schema_path: Optional[str] = None):
        """Initialize summary builder.

        Args:
            metrics_data: Metrics data to summarize
            schema_path: Optional path to JSON schema for validation
        """
        self.metrics_data = metrics_data
        self.schema_path = schema_path
        self.summary: Dict[str, Any] = {}

    def build_summary(self) -> Dict[str, Any]:
        """Build summary from metrics data.

        Returns:
            Summary of metrics data
        """
        log.info("Building summary from %d metrics runs", len(self.metrics_data.runs))

        # Calculate overall score
        overall_score = self._calculate_overall_score()

        # Calculate metrics summary
        metrics_summary = self._calculate_metrics_summary()

        # Build summary
        self.summary = {
            "overall_score": overall_score,
            "metrics": metrics_summary,
            "total_runs": len(self.metrics_data.runs),
            "collection_timestamp": self.metrics_data.collection_timestamp,
        }

        # Validate if schema is provided
        if self.schema_path:
            try:
                validate_metrics_data(self.summary, Path(self.schema_path))
                log.info("Summary validated against schema")
            except Exception as e:
                log.warning("Summary validation failed: %s", e)

        return self.summary

    def _calculate_overall_score(self) -> float:
        """Calculate overall score from metrics.

        Returns:
            Overall score (0.0 to 1.0)
        """
        if not self.metrics_data.runs:
            return 0.0

        # Calculate weighted average of all metrics
        total_weight = 0.0
        weighted_sum = 0.0

        for run in self.metrics_data.runs:
            for metric_name, metric_value in run.metrics.items():
                # Use metric value as weight (assuming higher values are better)
                weight = float(metric_value)
                total_weight += weight
                weighted_sum += metric_value * weight

        if total_weight == 0.0:
            return 0.0

        overall_score = weighted_sum / total_weight

        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, overall_score))

    def _calculate_metrics_summary(self) -> Dict[str, Any]:
        """Calculate summary for each metric.

        Returns:
            Summary of metrics
        """
        if not self.metrics_data.runs:
            return {}

        # Collect all metric values
        all_metrics = {}
        for run in self.metrics_data.runs:
            for metric_name, metric_value in run.metrics.items():
                if metric_name not in all_metrics:
                    all_metrics[metric_name] = []
                all_metrics[metric_name].append(metric_value)

        # Calculate statistics for each metric
        summary_metrics = {}
        for metric_name, values in all_metrics.items():
            if values:
                summary_metrics[metric_name] = {
                    "value": sum(values) / len(values),  # Average
                    "weighted_avg": self._calculate_weighted_average(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }

        return summary_metrics

    def _calculate_weighted_average(self, values: List[float]) -> float:
        """Calculate weighted average of values.

        Args:
            values: List of values

        Returns:
            Weighted average
        """
        if not values:
            return 0.0

        # Use values as weights
        total_weight = sum(values)
        if total_weight == 0.0:
            return 0.0

        weighted_sum = sum(v * v for v in values)
        return weighted_sum / total_weight

    def save_summary(self, output_path: Path) -> None:
        """Save summary to file.

        Args:
            output_path: Path to save summary to
        """
        try:
            with open(output_path, "w") as f:
                json.dump(self.summary, f, indent=2)
            log.info("Saved summary to %s", output_path)
        except Exception as e:
            log.error("Failed to save summary: %s", e)
            raise

    def get_summary(self) -> Dict[str, Any]:
        """Get summary.

        Returns:
            Summary of metrics data
        """
        return self.summary

    def get_overall_score(self) -> float:
        """Get overall score.

        Returns:
            Overall score (0.0 to 1.0)
        """
        return self.summary.get("overall_score", 0.0)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary.

        Returns:
            Summary of metrics
        """
        return self.summary.get("metrics", {})

    def get_total_runs(self) -> int:
        """Get total number of runs.

        Returns:
            Total number of runs
        """
        return self.summary.get("total_runs", 0)

    def get_collection_timestamp(self) -> str:
        """Get collection timestamp.

        Returns:
            Collection timestamp
        """
        return self.summary.get("collection_timestamp", "")

    def validate_summary(self) -> bool:
        """Validate summary against schema.

        Returns:
            True if valid, False otherwise
        """
        if not self.schema_path:
            return True

        try:
            validate_metrics_data(self.summary, Path(self.schema_path))
            return True
        except Exception as e:
            log.error("Summary validation failed: %s", e)
            return False
