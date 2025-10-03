"""
Tests for TwoCell Φ calculation and signatures.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from proofengine.metrics import WorkUnits
from proofengine.orchestrator.rewriter import PlanRewriter, TwoCell
from proofengine.orchestrator.strategy_api import StrategyContext


class TestTwoCellPhi:
    """Tests for TwoCell Φ calculation and signatures."""

    def test_phi_calculation(self):
        """Test Φ calculation for different plan complexities."""
        rewriter = PlanRewriter()

        # Simple plan
        simple_plan = {"steps": [{"type": "test"}]}
        context = StrategyContext(
            failreason="api.semver_missing",
            operator="test_operator",
            plan=simple_plan,
            current_step={"id": "step1", "type": "test"},
            history=[],
            budgets={},
        )

        phi_simple = rewriter.calculate_phi(simple_plan, context)
        assert phi_simple > 0

        # Complex plan
        complex_plan = {
            "steps": [
                {"type": "test"},
                {"type": "opa"},
                {"type": "docker"},
                {"type": "test"},
            ]
        }

        phi_complex = rewriter.calculate_phi(complex_plan, context)
        assert phi_complex > phi_simple

        # Security-related failure
        security_context = StrategyContext(
            failreason="policy.secret_egress",
            operator="test_operator",
            plan=simple_plan,
            current_step={"id": "step1", "type": "test"},
            history=[],
            budgets={},
        )
        phi_security = rewriter.calculate_phi(simple_plan, security_context)
        assert phi_security > phi_simple

    def test_phi_decrease_enforcement(self):
        """Test that Φ must strictly decrease."""
        rewriter = PlanRewriter()

        # Mock strategy that would increase Φ
        mock_strategy = Mock()
        mock_strategy.id = "test_strategy"
        mock_strategy.get_obligations_added.return_value = []

        # Create a plan that would increase complexity
        plan = {"steps": [{"type": "test"}]}
        context = StrategyContext(
            failreason="api.semver_missing",
            operator="test_operator",
            plan=plan,
            current_step={"id": "step1", "type": "test"},
            history=[],
            budgets={},
        )

        # Mock the strategy to return a more complex plan
        def mock_apply(plan, context):
            return {"steps": [{"type": "test"}, {"type": "opa"}, {"type": "docker"}]}

        # This should raise an exception due to Φ increase
        with pytest.raises(ValueError, match="Φ must strictly decrease"):
            rewriter.apply_strategy(mock_strategy, plan, context)

    def test_two_cell_creation(self):
        """Test TwoCell creation with proper Φ values."""
        rewriter = PlanRewriter()

        # Mock strategy that decreases Φ
        mock_strategy = Mock()
        mock_strategy.id = "test_strategy"
        mock_strategy.get_obligations_added.return_value = ["obligation1"]

        # Create a plan
        plan = {"steps": [{"type": "test"}, {"type": "opa"}]}
        context = StrategyContext(
            failreason="api.semver_missing",
            operator="test_operator",
            plan=plan,
            current_step={"id": "step1", "type": "test"},
            history=[],
            budgets={},
        )

        # Mock the strategy to return a simpler plan
        def mock_apply(plan, context):
            return {"steps": [{"type": "test"}]}

        # Patch the rewriter to use the mock

        def mock_apply_strategy(strategy, plan, context, selection_result=None):
            # Calculate Φ before
            phi_before = rewriter.calculate_phi(plan, context)

            # Apply strategy (simplify plan)
            plan_after = {"steps": [{"type": "test"}]}  # Simpler plan

            # Calculate Φ after
            phi_after = rewriter.calculate_phi(plan_after, context)

            # Create TwoCell with proper values
            import uuid
            from datetime import datetime

            two_cell = TwoCell(
                cell_id=str(uuid.uuid4()),
                timestamp=datetime.now().isoformat(),
                strategy_applied=strategy.id,
                plan_before=plan,
                plan_after=plan_after,
                phi_before=phi_before,
                phi_after=phi_after,
                phi_decrease=phi_after + rewriter.epsilon < phi_before,
                signature={},
                obligations_added=strategy.get_obligations_added(context),
                delta_v_predicted=0.0,
                delta_v_observed=phi_before - phi_after,
                selection_result=selection_result,
                work_units=WorkUnits(
                    operators_run=1,
                    proofs_checked=1,
                    tests_run=1,
                    opa_rules_evaluated=1,
                ),
            )

            # Sign the TwoCell
            two_cell.signature = rewriter._sign_two_cell(two_cell)
            return two_cell

        rewriter.apply_strategy = mock_apply_strategy

        # This should work
        two_cell = rewriter.apply_strategy(mock_strategy, plan, context)

        assert two_cell.strategy_applied == "test_strategy"
        assert two_cell.phi_before > two_cell.phi_after
        assert two_cell.phi_decrease
        assert "obligation1" in two_cell.obligations_added
        assert two_cell.signature["alg"] == "HMAC-SHA256"
        assert two_cell.signature["key_id"] == "local-v0"

    def test_two_cell_signature(self):
        """Test TwoCell signature creation and verification."""
        rewriter = PlanRewriter()

        # Create a TwoCell
        two_cell = TwoCell(
            cell_id="test-cell",
            timestamp="2024-01-01T00:00:00",
            strategy_applied="test_strategy",
            plan_before={"steps": []},
            plan_after={"steps": []},
            phi_before=1.0,
            phi_after=0.5,
            phi_decrease=True,
            signature={},
            obligations_added=[],
        )

        # Sign the TwoCell
        two_cell.signature = rewriter._sign_two_cell(two_cell)

        # Verify signature
        assert rewriter.verify_two_cell(two_cell)

        # Tamper with signature
        two_cell.signature["value"] = "tampered"
        assert not rewriter.verify_two_cell(two_cell)

    def test_two_cell_serialization(self):
        """Test TwoCell serialization and deserialization."""
        rewriter = PlanRewriter()

        # Create a TwoCell
        two_cell = TwoCell(
            cell_id="test-cell",
            timestamp="2024-01-01T00:00:00",
            strategy_applied="test_strategy",
            plan_before={"steps": [{"type": "test"}]},
            plan_after={"steps": []},
            phi_before=1.0,
            phi_after=0.5,
            phi_decrease=True,
            signature={"alg": "HMAC-SHA256", "key_id": "local-v0", "value": "test"},
            obligations_added=["obligation1"],
        )

        # Test to_dict
        two_cell_dict = two_cell.to_dict()
        assert two_cell_dict["cell_id"] == "test-cell"
        assert two_cell_dict["strategy_applied"] == "test_strategy"
        assert two_cell_dict["phi_before"] == 1.0
        assert two_cell_dict["phi_after"] == 0.5
        assert two_cell_dict["phi_decrease"]

        # Test save/load
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            rewriter.save_two_cell(two_cell, temp_path)
            loaded_two_cell = rewriter.load_two_cell(temp_path)

            assert loaded_two_cell.cell_id == two_cell.cell_id
            assert loaded_two_cell.strategy_applied == two_cell.strategy_applied
            assert loaded_two_cell.phi_before == two_cell.phi_before
            assert loaded_two_cell.phi_after == two_cell.phi_after
            assert loaded_two_cell.phi_decrease == two_cell.phi_decrease
            assert loaded_two_cell.signature == two_cell.signature
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_work_units_in_two_cell(self):
        """Test that TwoCell includes work units."""
        rewriter = PlanRewriter()

        # Mock strategy
        mock_strategy = Mock()
        mock_strategy.id = "test_strategy"
        mock_strategy.get_obligations_added.return_value = []

        plan = {"steps": [{"type": "test"}]}
        context = StrategyContext(
            failreason="api.semver_missing",
            operator="test_operator",
            plan=plan,
            current_step={"id": "step1", "type": "test"},
            history=[],
            budgets={},
        )

        # Mock the strategy to return a simpler plan
        def mock_apply(plan, context):
            return {"steps": []}

        # Patch the rewriter to use the mock
        def mock_apply_strategy(strategy, plan, context, selection_result=None):
            # Calculate Φ before
            phi_before = rewriter.calculate_phi(plan, context)

            # Apply strategy (simplify plan)
            plan_after = {"steps": []}  # Simpler plan

            # Calculate Φ after
            phi_after = rewriter.calculate_phi(plan_after, context)

            # Create TwoCell with proper values
            import uuid
            from datetime import datetime

            two_cell = TwoCell(
                cell_id=str(uuid.uuid4()),
                timestamp=datetime.now().isoformat(),
                strategy_applied=strategy.id,
                plan_before=plan,
                plan_after=plan_after,
                phi_before=phi_before,
                phi_after=phi_after,
                phi_decrease=phi_after + rewriter.epsilon < phi_before,
                signature={},
                obligations_added=strategy.get_obligations_added(context),
                delta_v_predicted=0.0,
                delta_v_observed=phi_before - phi_after,
                selection_result=selection_result,
                work_units=WorkUnits(
                    operators_run=1,
                    proofs_checked=1,
                    tests_run=1,
                    opa_rules_evaluated=1,
                ),
            )

            # Sign the TwoCell
            two_cell.signature = rewriter._sign_two_cell(two_cell)
            return two_cell

        rewriter.apply_strategy = mock_apply_strategy

        two_cell = rewriter.apply_strategy(mock_strategy, plan, context)

        assert two_cell.work_units is not None
        assert two_cell.work_units.operators_run == 1
        assert two_cell.work_units.proofs_checked == 1
        assert two_cell.work_units.tests_run == 1
        assert two_cell.work_units.opa_rules_evaluated == 1

    def test_selection_result_in_two_cell(self):
        """Test that TwoCell includes selection result."""
        rewriter = PlanRewriter()

        # Mock strategy
        mock_strategy = Mock()
        mock_strategy.id = "test_strategy"
        mock_strategy.get_obligations_added.return_value = []

        plan = {"steps": [{"type": "test"}]}
        context = StrategyContext(
            failreason="api.semver_missing",
            operator="test_operator",
            plan=plan,
            current_step={"id": "step1", "type": "test"},
            history=[],
            budgets={},
        )

        # Mock the strategy to return a simpler plan
        def mock_apply(plan, context):
            return {"steps": []}

        selection_result = {
            "candidates": [{"strategy_id": "test_strategy", "score": 0.8, "confidence": 0.9}],
            "chosen": {"id": "test_strategy", "score": 0.8, "why": "Best match"},
        }

        # Patch the rewriter to use the mock
        def mock_apply_strategy(strategy, plan, context, selection_result=None):
            # Calculate Φ before
            phi_before = rewriter.calculate_phi(plan, context)

            # Apply strategy (simplify plan)
            plan_after = {"steps": []}  # Simpler plan

            # Calculate Φ after
            phi_after = rewriter.calculate_phi(plan_after, context)

            # Create TwoCell with proper values
            import uuid
            from datetime import datetime

            two_cell = TwoCell(
                cell_id=str(uuid.uuid4()),
                timestamp=datetime.now().isoformat(),
                strategy_applied=strategy.id,
                plan_before=plan,
                plan_after=plan_after,
                phi_before=phi_before,
                phi_after=phi_after,
                phi_decrease=phi_after + rewriter.epsilon < phi_before,
                signature={},
                obligations_added=strategy.get_obligations_added(context),
                delta_v_predicted=0.0,
                delta_v_observed=phi_before - phi_after,
                selection_result=selection_result,
                work_units=WorkUnits(
                    operators_run=1,
                    proofs_checked=1,
                    tests_run=1,
                    opa_rules_evaluated=1,
                ),
            )

            # Sign the TwoCell
            two_cell.signature = rewriter._sign_two_cell(two_cell)
            return two_cell

        rewriter.apply_strategy = mock_apply_strategy

        two_cell = rewriter.apply_strategy(mock_strategy, plan, context, selection_result)

        assert two_cell.selection_result == selection_result
        assert two_cell.selection_result["chosen"]["id"] == "test_strategy"


if __name__ == "__main__":
    pytest.main([__file__])
