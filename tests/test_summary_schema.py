#!/usr/bin/env python3
"""
Tests for summary.json schema validation and consistency.
"""
import json
import pytest
from pathlib import Path
from typing import Dict, Any, List

import fastjsonschema
from pefc.metrics.collect import MetricsCollector
from pefc.metrics.aggregate import MetricsAggregator


class TestSummarySchema:
    """Test summary.json schema validation and consistency."""

    def test_summary_schema_validation(self, sample_metrics_data: List[Dict[str, Any]]):
        """Test that generated summary.json validates against schema."""
        # Load schema
        schema_path = Path("schema/summary.schema.json")
        if not schema_path.exists():
            pytest.skip("Summary schema not found")

        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Create validator
        validator = fastjsonschema.compile(schema)

        # Generate summary from sample data
        collector = MetricsCollector()
        for data in sample_metrics_data:
            collector.add_run(data)

        aggregator = MetricsAggregator()
        summary = aggregator.aggregate(collector.get_runs())

        # Validate summary against schema
        try:
            validator(summary)
        except fastjsonschema.JsonSchemaValueException as e:
            pytest.fail(f"Summary validation failed: {e}")

    def test_bounded_metrics_constraints(self, sample_metrics_data: List[Dict[str, Any]]):
        """Test that bounded metrics are constrained to [0,1]."""
        # Add out-of-bounds metrics
        test_data = sample_metrics_data.copy()
        test_data.append(
            {
                "run_id": "out_of_bounds",
                "timestamp": "2025-01-01T00:03:00Z",
                "metrics": {
                    "coverage_gain": 1.5,  # > 1.0
                    "novelty_avg": -0.1,  # < 0.0
                    "n_items": 50,
                },
            }
        )

        collector = MetricsCollector()
        for data in test_data:
            collector.add_run(data)

        aggregator = MetricsAggregator()
        summary = aggregator.aggregate(collector.get_runs())

        # Check that bounded metrics are constrained
        assert 0.0 <= summary["overall"]["coverage_gain"] <= 1.0
        assert 0.0 <= summary["overall"]["novelty_avg"] <= 1.0

    def test_weighted_average_consistency(self, test_runs: List[Dict[str, Any]]):
        """Test that weighted averages are consistent with manual calculation."""
        collector = MetricsCollector()
        for run in test_runs:
            collector.add_run(run)

        aggregator = MetricsAggregator()
        summary = aggregator.aggregate(collector.get_runs())

        # Manual calculation of weighted average
        total_weight = sum(run["metrics"]["n_items"] for run in test_runs)
        expected_coverage = (
            sum(run["metrics"]["coverage_gain"] * run["metrics"]["n_items"] for run in test_runs)
            / total_weight
        )

        # Check consistency (allow small floating point differences)
        assert abs(summary["overall"]["coverage_gain"] - expected_coverage) < 1e-6

    def test_no_double_counting(self, sample_metrics_data: List[Dict[str, Any]]):
        """Test that adding the same run twice doesn't double-count."""
        collector = MetricsCollector()

        # Add runs
        for data in sample_metrics_data:
            collector.add_run(data)

        # Add same runs again
        for data in sample_metrics_data:
            collector.add_run(data)

        aggregator = MetricsAggregator()
        summary = aggregator.aggregate(collector.get_runs())

        # Should have same count as original data
        assert summary["overall"]["run_count"] == len(sample_metrics_data)

    def test_aggregate_consistency(self, test_runs: List[Dict[str, Any]]):
        """Test that aggregate values are consistent with individual runs."""
        collector = MetricsCollector()
        for run in test_runs:
            collector.add_run(run)

        aggregator = MetricsAggregator()
        summary = aggregator.aggregate(collector.get_runs())

        # Check that aggregate values make sense
        assert summary["overall"]["run_count"] == len(test_runs)
        assert summary["overall"]["total_items"] == sum(
            run["metrics"]["n_items"] for run in test_runs
        )

        # Check that averages are within reasonable bounds
        coverage_values = [run["metrics"]["coverage_gain"] for run in test_runs]
        assert min(coverage_values) <= summary["overall"]["coverage_gain"] <= max(coverage_values)

    def test_schema_required_fields(self, sample_metrics_data: List[Dict[str, Any]]):
        """Test that summary contains all required schema fields."""
        collector = MetricsCollector()
        for data in sample_metrics_data:
            collector.add_run(data)

        aggregator = MetricsAggregator()
        summary = aggregator.aggregate(collector.get_runs())

        # Check required fields
        required_fields = ["overall", "runs"]
        for field in required_fields:
            assert field in summary, f"Missing required field: {field}"

        # Check overall section
        overall_required = ["run_count", "total_items", "coverage_gain", "novelty_avg"]
        for field in overall_required:
            assert field in summary["overall"], f"Missing overall field: {field}"

    def test_empty_data_handling(self):
        """Test handling of empty metrics data."""
        collector = MetricsCollector()
        aggregator = MetricsAggregator()
        summary = aggregator.aggregate(collector.get_runs())

        # Should handle empty data gracefully
        assert summary["overall"]["run_count"] == 0
        assert summary["overall"]["total_items"] == 0
        assert summary["runs"] == []

    def test_metric_bounds_enforcement(self, sample_metrics_data: List[Dict[str, Any]]):
        """Test that metric bounds are properly enforced."""
        # Create data with out-of-bounds values
        test_data = sample_metrics_data.copy()
        test_data.append(
            {
                "run_id": "extreme_values",
                "timestamp": "2025-01-01T00:03:00Z",
                "metrics": {
                    "coverage_gain": 2.0,  # Way out of bounds
                    "novelty_avg": -1.0,  # Way out of bounds
                    "n_items": 1000,
                },
            }
        )

        collector = MetricsCollector()
        for data in test_data:
            collector.add_run(data)

        aggregator = MetricsAggregator()
        summary = aggregator.aggregate(collector.get_runs())

        # Bounded metrics should be constrained
        assert 0.0 <= summary["overall"]["coverage_gain"] <= 1.0
        assert 0.0 <= summary["overall"]["novelty_avg"] <= 1.0

    def test_schema_validation_error_handling(self):
        """Test that invalid summary data is properly rejected."""
        schema_path = Path("schema/summary.schema.json")
        if not schema_path.exists():
            pytest.skip("Summary schema not found")

        with open(schema_path, "r") as f:
            schema = json.load(f)

        validator = fastjsonschema.compile(schema)

        # Test invalid data
        invalid_summary = {
            "overall": {
                "run_count": -1,  # Invalid negative count
                "total_items": "not_a_number",  # Invalid type
            },
            "runs": "not_a_list",  # Invalid type
        }

        with pytest.raises(fastjsonschema.JsonSchemaValueException):
            validator(invalid_summary)

    def test_summary_reproducibility(self, test_runs: List[Dict[str, Any]]):
        """Test that summary generation is reproducible."""
        collector1 = MetricsCollector()
        collector2 = MetricsCollector()

        for run in test_runs:
            collector1.add_run(run)
            collector2.add_run(run)

        aggregator = MetricsAggregator()
        summary1 = aggregator.aggregate(collector1.get_runs())
        summary2 = aggregator.aggregate(collector2.get_runs())

        # Should be identical
        assert summary1 == summary2

    @pytest.mark.slow
    def test_large_dataset_handling(self, large_test_runs: List[Dict[str, Any]]):
        """Test handling of large datasets."""
        collector = MetricsCollector()
        for run in large_test_runs:
            collector.add_run(run)

        aggregator = MetricsAggregator()
        summary = aggregator.aggregate(collector.get_runs())

        # Should handle large datasets without issues
        assert summary["overall"]["run_count"] == len(large_test_runs)
        assert summary["overall"]["total_items"] == sum(
            run["metrics"]["n_items"] for run in large_test_runs
        )

        # Performance should be reasonable (this is a basic check)
        assert len(summary["runs"]) == len(large_test_runs)
