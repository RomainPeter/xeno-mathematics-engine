"""
Tests for metrics fairness guarantees.
"""

import pytest
import json
import tempfile
from pathlib import Path

from proofengine.metrics import (
    ExecutionMetrics,
    WorkUnits,
    TimeBreakdown,
    CacheInfo,
    compare_metrics_fairness,
    enforce_fairness_gate,
)
from proofengine.orchestrator.modes import BaselineMode


class TestMetricsFairness:
    """Tests for metrics fairness guarantees."""

    def test_work_units_equality(self):
        """Test WorkUnits equality comparison."""
        wu1 = WorkUnits(operators_run=1, proofs_checked=1, tests_run=1, opa_rules_evaluated=1)
        wu2 = WorkUnits(operators_run=1, proofs_checked=1, tests_run=1, opa_rules_evaluated=1)
        wu3 = WorkUnits(operators_run=2, proofs_checked=1, tests_run=1, opa_rules_evaluated=1)

        assert wu1 == wu2
        assert wu1 != wu3
        assert wu2 != wu3

    def test_execution_metrics_creation(self):
        """Test ExecutionMetrics creation."""
        work_units = WorkUnits(
            operators_run=1, proofs_checked=1, tests_run=1, opa_rules_evaluated=1
        )
        time_breakdown = TimeBreakdown(
            t_orchestrator_ms=100.0, t_llm_ms=0.0, t_verifier_ms=50.0, t_io_ms=10.0
        )
        cache_info = CacheInfo(cache_used=False, cache_hits={"opa": 0, "sbom": 0, "llm": 0})

        metrics = ExecutionMetrics(
            work_units=work_units,
            time_breakdown=time_breakdown,
            cache_info=cache_info,
            steps_count=1,
            rewrites_applied=0,
            phi_delta=0.0,
            mode="baseline",
        )

        assert metrics.work_units == work_units
        assert metrics.time_breakdown == time_breakdown
        assert metrics.cache_info == cache_info
        assert metrics.mode == "baseline"

    def test_metrics_serialization(self):
        """Test metrics serialization and deserialization."""
        work_units = WorkUnits(
            operators_run=1, proofs_checked=1, tests_run=1, opa_rules_evaluated=1
        )
        time_breakdown = TimeBreakdown(
            t_orchestrator_ms=100.0, t_llm_ms=0.0, t_verifier_ms=50.0, t_io_ms=10.0
        )
        cache_info = CacheInfo(cache_used=False, cache_hits={"opa": 0, "sbom": 0, "llm": 0})

        metrics = ExecutionMetrics(
            work_units=work_units,
            time_breakdown=time_breakdown,
            cache_info=cache_info,
            steps_count=1,
            rewrites_applied=0,
            phi_delta=0.0,
            mode="baseline",
        )

        # Test to_dict
        metrics_dict = metrics.to_dict()
        assert "work_units" in metrics_dict
        assert "time_breakdown" in metrics_dict
        assert "cache_info" in metrics_dict
        assert metrics_dict["mode"] == "baseline"

        # Test save/load
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            metrics.save_fair_metrics(temp_path)
            loaded_metrics = ExecutionMetrics.load_fair_metrics(temp_path)

            assert loaded_metrics.work_units == metrics.work_units
            assert (
                loaded_metrics.time_breakdown.t_orchestrator_ms
                == metrics.time_breakdown.t_orchestrator_ms
            )
            assert loaded_metrics.cache_info.cache_used == metrics.cache_info.cache_used
            assert loaded_metrics.mode == metrics.mode
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_fairness_comparison(self):
        """Test fairness comparison between baseline and active metrics."""
        # Identical work units - should pass
        baseline_work = WorkUnits(
            operators_run=1, proofs_checked=1, tests_run=1, opa_rules_evaluated=1
        )
        active_work = WorkUnits(
            operators_run=1, proofs_checked=1, tests_run=1, opa_rules_evaluated=1
        )

        baseline_metrics = ExecutionMetrics(
            work_units=baseline_work,
            time_breakdown=TimeBreakdown(),
            cache_info=CacheInfo(),
            mode="baseline",
        )

        active_metrics = ExecutionMetrics(
            work_units=active_work,
            time_breakdown=TimeBreakdown(),
            cache_info=CacheInfo(),
            mode="active",
        )

        assert compare_metrics_fairness(baseline_metrics, active_metrics)

        # Different work units - should fail
        different_work = WorkUnits(
            operators_run=2, proofs_checked=1, tests_run=1, opa_rules_evaluated=1
        )
        different_metrics = ExecutionMetrics(
            work_units=different_work,
            time_breakdown=TimeBreakdown(),
            cache_info=CacheInfo(),
            mode="active",
        )

        assert not compare_metrics_fairness(baseline_metrics, different_metrics)

    def test_fairness_gate_success(self):
        """Test fairness gate with identical work units."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_path = Path(temp_dir) / "baseline.json"
            active_path = Path(temp_dir) / "active.json"

            # Create identical metrics
            work_units = WorkUnits(
                operators_run=1, proofs_checked=1, tests_run=1, opa_rules_evaluated=1
            )

            baseline_metrics = ExecutionMetrics(
                work_units=work_units,
                time_breakdown=TimeBreakdown(),
                cache_info=CacheInfo(),
                mode="baseline",
            )

            active_metrics = ExecutionMetrics(
                work_units=work_units,
                time_breakdown=TimeBreakdown(),
                cache_info=CacheInfo(),
                mode="active",
            )

            baseline_metrics.save_fair_metrics(str(baseline_path))
            active_metrics.save_fair_metrics(str(active_path))

            # Should not raise exception
            enforce_fairness_gate(str(baseline_path), str(active_path))

    def test_fairness_gate_failure(self):
        """Test fairness gate with different work units."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_path = Path(temp_dir) / "baseline.json"
            active_path = Path(temp_dir) / "active.json"

            # Create different metrics
            baseline_work = WorkUnits(
                operators_run=1, proofs_checked=1, tests_run=1, opa_rules_evaluated=1
            )
            active_work = WorkUnits(
                operators_run=2, proofs_checked=1, tests_run=1, opa_rules_evaluated=1
            )

            baseline_metrics = ExecutionMetrics(
                work_units=baseline_work,
                time_breakdown=TimeBreakdown(),
                cache_info=CacheInfo(),
                mode="baseline",
            )

            active_metrics = ExecutionMetrics(
                work_units=active_work,
                time_breakdown=TimeBreakdown(),
                cache_info=CacheInfo(),
                mode="active",
            )

            baseline_metrics.save_fair_metrics(str(baseline_path))
            active_metrics.save_fair_metrics(str(active_path))

            # Should raise SystemExit
            with pytest.raises(SystemExit):
                enforce_fairness_gate(str(baseline_path), str(active_path))

    def test_baseline_mode_fairness(self):
        """Test baseline mode with fairness metrics."""
        baseline_mode = BaselineMode()

        # Mock plan and state
        plan_path = "test_plan.json"
        state_path = "test_state.json"

        # Create temporary files
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            plan_path = f.name
            json.dump({"steps": [{"type": "test"}]}, f)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state_path = f.name
            json.dump({"state": "test"}, f)

        try:
            result = baseline_mode.run(plan_path, state_path)

            assert result["mode"] == "baseline"
            assert not result["two_cat_enabled"]
            assert "metrics" in result

            metrics = result["metrics"]
            assert isinstance(metrics, ExecutionMetrics)
            assert metrics.mode == "baseline"
            assert metrics.work_units.operators_run == 1
            assert metrics.rewrites_applied == 0  # No rewrites in baseline
        finally:
            Path(plan_path).unlink(missing_ok=True)
            Path(state_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__])
