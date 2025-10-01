#!/usr/bin/env python3
"""
Tests for metrics aggregation parity across backends.
"""
import pytest
from typing import List, Dict, Any
from unittest.mock import patch

from pefc.metrics.aggregate import MetricsAggregator
from pefc.metrics.collect import MetricsCollector


def _has_pandas():
    """Check if pandas is available."""
    try:
        import importlib.util

        return importlib.util.find_spec("pandas") is not None
    except ImportError:
        return False


def _has_polars():
    """Check if polars is available."""
    try:
        import importlib.util

        return importlib.util.find_spec("polars") is not None
    except ImportError:
        return False


class TestMetricsAggregationParity:
    """Test parity between different aggregation backends."""

    def test_python_backend_basic(self, test_runs: List[Dict[str, Any]]):
        """Test basic Python backend aggregation."""
        collector = MetricsCollector()
        for run in test_runs:
            collector.add_run(run)

        aggregator = MetricsAggregator(backend="python")
        summary = aggregator.aggregate(collector.get_runs())

        # Basic checks
        assert summary["overall"]["run_count"] == len(test_runs)
        assert summary["overall"]["total_items"] == sum(
            run["metrics"]["n_items"] for run in test_runs
        )
        assert "coverage_gain" in summary["overall"]
        assert "novelty_avg" in summary["overall"]

    @pytest.mark.skipif(not _has_pandas(), reason="pandas not available")
    def test_pandas_backend_basic(self, test_runs: List[Dict[str, Any]]):
        """Test basic pandas backend aggregation."""
        collector = MetricsCollector()
        for run in test_runs:
            collector.add_run(run)

        aggregator = MetricsAggregator(backend="pandas")
        summary = aggregator.aggregate(collector.get_runs())

        # Basic checks
        assert summary["overall"]["run_count"] == len(test_runs)
        assert summary["overall"]["total_items"] == sum(
            run["metrics"]["n_items"] for run in test_runs
        )
        assert "coverage_gain" in summary["overall"]
        assert "novelty_avg" in summary["overall"]

    @pytest.mark.skipif(not _has_polars(), reason="polars not available")
    def test_polars_backend_basic(self, test_runs: List[Dict[str, Any]]):
        """Test basic polars backend aggregation."""
        collector = MetricsCollector()
        for run in test_runs:
            collector.add_run(run)

        aggregator = MetricsAggregator(backend="polars")
        summary = aggregator.aggregate(collector.get_runs())

        # Basic checks
        assert summary["overall"]["run_count"] == len(test_runs)
        assert summary["overall"]["total_items"] == sum(
            run["metrics"]["n_items"] for run in test_runs
        )
        assert "coverage_gain" in summary["overall"]
        assert "novelty_avg" in summary["overall"]

    def test_python_pandas_parity(self, test_runs: List[Dict[str, Any]]):
        """Test parity between Python and pandas backends."""
        if not _has_pandas():
            pytest.skip("pandas not available")

        collector = MetricsCollector()
        for run in test_runs:
            collector.add_run(run)

        # Get results from both backends
        python_agg = MetricsAggregator(backend="python")
        pandas_agg = MetricsAggregator(backend="pandas")

        python_summary = python_agg.aggregate(collector.get_runs())
        pandas_summary = pandas_agg.aggregate(collector.get_runs())

        # Compare key metrics (allow small floating point differences)
        assert python_summary["overall"]["run_count"] == pandas_summary["overall"]["run_count"]
        assert python_summary["overall"]["total_items"] == pandas_summary["overall"]["total_items"]

        # Compare weighted averages
        assert (
            abs(
                python_summary["overall"]["coverage_gain"]
                - pandas_summary["overall"]["coverage_gain"]
            )
            < 1e-6
        )
        assert (
            abs(python_summary["overall"]["novelty_avg"] - pandas_summary["overall"]["novelty_avg"])
            < 1e-6
        )

    def test_python_polars_parity(self, test_runs: List[Dict[str, Any]]):
        """Test parity between Python and polars backends."""
        if not _has_polars():
            pytest.skip("polars not available")

        collector = MetricsCollector()
        for run in test_runs:
            collector.add_run(run)

        # Get results from both backends
        python_agg = MetricsAggregator(backend="python")
        polars_agg = MetricsAggregator(backend="polars")

        python_summary = python_agg.aggregate(collector.get_runs())
        polars_summary = polars_agg.aggregate(collector.get_runs())

        # Compare key metrics (allow small floating point differences)
        assert python_summary["overall"]["run_count"] == polars_summary["overall"]["run_count"]
        assert python_summary["overall"]["total_items"] == polars_summary["overall"]["total_items"]

        # Compare weighted averages
        assert (
            abs(
                python_summary["overall"]["coverage_gain"]
                - polars_summary["overall"]["coverage_gain"]
            )
            < 1e-6
        )
        assert (
            abs(python_summary["overall"]["novelty_avg"] - polars_summary["overall"]["novelty_avg"])
            < 1e-6
        )

    def test_pandas_polars_parity(self, test_runs: List[Dict[str, Any]]):
        """Test parity between pandas and polars backends."""
        if not _has_pandas() or not _has_polars():
            pytest.skip("pandas or polars not available")

        collector = MetricsCollector()
        for run in test_runs:
            collector.add_run(run)

        # Get results from both backends
        pandas_agg = MetricsAggregator(backend="pandas")
        polars_agg = MetricsAggregator(backend="polars")

        pandas_summary = pandas_agg.aggregate(collector.get_runs())
        polars_summary = polars_agg.aggregate(collector.get_runs())

        # Compare key metrics (allow small floating point differences)
        assert pandas_summary["overall"]["run_count"] == polars_summary["overall"]["run_count"]
        assert pandas_summary["overall"]["total_items"] == polars_summary["overall"]["total_items"]

        # Compare weighted averages
        assert (
            abs(
                pandas_summary["overall"]["coverage_gain"]
                - polars_summary["overall"]["coverage_gain"]
            )
            < 1e-6
        )
        assert (
            abs(pandas_summary["overall"]["novelty_avg"] - polars_summary["overall"]["novelty_avg"])
            < 1e-6
        )

    def test_auto_backend_selection(self, test_runs: List[Dict[str, Any]]):
        """Test automatic backend selection."""
        collector = MetricsCollector()
        for run in test_runs:
            collector.add_run(run)

        # Test auto backend
        aggregator = MetricsAggregator(backend="auto")
        summary = aggregator.aggregate(collector.get_runs())

        # Should work regardless of available backends
        assert summary["overall"]["run_count"] == len(test_runs)
        assert summary["overall"]["total_items"] == sum(
            run["metrics"]["n_items"] for run in test_runs
        )

    def test_backend_fallback(self, test_runs: List[Dict[str, Any]]):
        """Test backend fallback when preferred backend is not available."""
        collector = MetricsCollector()
        for run in test_runs:
            collector.add_run(run)

        # Test with unavailable backend (should fallback to python)
        with patch("pefc.metrics.aggregate._has_pandas", return_value=False):
            with patch("pefc.metrics.aggregate._has_polars", return_value=False):
                aggregator = MetricsAggregator(backend="pandas")
                summary = aggregator.aggregate(collector.get_runs())

                # Should still work with fallback
                assert summary["overall"]["run_count"] == len(test_runs)

    def test_weighted_average_consistency(self, test_runs: List[Dict[str, Any]]):
        """Test that weighted averages are consistent across backends."""
        collector = MetricsCollector()
        for run in test_runs:
            collector.add_run(run)

        backends = ["python"]
        if _has_pandas():
            backends.append("pandas")
        if _has_polars():
            backends.append("polars")

        summaries = {}
        for backend in backends:
            aggregator = MetricsAggregator(backend=backend)
            summaries[backend] = aggregator.aggregate(collector.get_runs())

        # Compare weighted averages across all available backends
        for backend1 in backends:
            for backend2 in backends:
                if backend1 != backend2:
                    summary1 = summaries[backend1]
                    summary2 = summaries[backend2]

                    assert (
                        abs(
                            summary1["overall"]["coverage_gain"]
                            - summary2["overall"]["coverage_gain"]
                        )
                        < 1e-6
                    )
                    assert (
                        abs(summary1["overall"]["novelty_avg"] - summary2["overall"]["novelty_avg"])
                        < 1e-6
                    )

    def test_empty_data_handling_parity(self):
        """Test that empty data is handled consistently across backends."""
        collector = MetricsCollector()

        backends = ["python"]
        if _has_pandas():
            backends.append("pandas")
        if _has_polars():
            backends.append("polars")

        summaries = {}
        for backend in backends:
            aggregator = MetricsAggregator(backend=backend)
            summaries[backend] = aggregator.aggregate(collector.get_runs())

        # All backends should handle empty data the same way
        for backend1 in backends:
            for backend2 in backends:
                if backend1 != backend2:
                    summary1 = summaries[backend1]
                    summary2 = summaries[backend2]

                    assert summary1["overall"]["run_count"] == summary2["overall"]["run_count"]
                    assert summary1["overall"]["total_items"] == summary2["overall"]["total_items"]

    @pytest.mark.slow
    def test_large_dataset_parity(self, large_test_runs: List[Dict[str, Any]]):
        """Test parity with large datasets."""
        collector = MetricsCollector()
        for run in large_test_runs:
            collector.add_run(run)

        backends = ["python"]
        if _has_pandas():
            backends.append("pandas")
        if _has_polars():
            backends.append("polars")

        summaries = {}
        for backend in backends:
            aggregator = MetricsAggregator(backend=backend)
            summaries[backend] = aggregator.aggregate(collector.get_runs())

        # Compare results across backends
        for backend1 in backends:
            for backend2 in backends:
                if backend1 != backend2:
                    summary1 = summaries[backend1]
                    summary2 = summaries[backend2]

                    assert summary1["overall"]["run_count"] == summary2["overall"]["run_count"]
                    assert summary1["overall"]["total_items"] == summary2["overall"]["total_items"]

                    # Weighted averages should be very close
                    assert (
                        abs(
                            summary1["overall"]["coverage_gain"]
                            - summary2["overall"]["coverage_gain"]
                        )
                        < 1e-6
                    )
