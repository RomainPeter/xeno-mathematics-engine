#!/usr/bin/env python3
"""
Metrics aggregation utilities.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging

from pefc.metrics.types import RunRecord

logger = logging.getLogger(__name__)


class MetricsAggregator:
    """Aggregates metrics from multiple runs."""

    def __init__(self, backend: str = "python"):
        """Initialize aggregator with specified backend."""
        self.backend = backend
        self.runs: List[RunRecord] = []

    def add_runs(self, runs: List[RunRecord]) -> None:
        """Add runs to aggregator."""
        self.runs.extend(runs)

    def aggregate(self, runs: Optional[List[RunRecord]] = None) -> Dict[str, Any]:
        """Aggregate metrics from runs."""
        if runs is not None:
            self.runs = runs

        if not self.runs:
            return {
                "overall": {
                    "run_count": 0,
                    "total_items": 0,
                    "coverage_gain": 0.0,
                    "novelty_avg": 0.0,
                }
            }

        # Calculate basic metrics
        total_items = sum(run.weight for run in self.runs)

        # Calculate weighted averages
        coverage_gain = 0.0
        novelty_avg = 0.0

        if total_items > 0:
            coverage_gain = (
                sum(run.get_metric("coverage_gain", 0.0) * run.weight for run in self.runs)
                / total_items
            )

            novelty_avg = (
                sum(run.get_metric("novelty_avg", 0.0) * run.weight for run in self.runs)
                / total_items
            )

        return {
            "overall": {
                "run_count": len(self.runs),
                "total_items": total_items,
                "coverage_gain": coverage_gain,
                "novelty_avg": novelty_avg,
            }
        }
