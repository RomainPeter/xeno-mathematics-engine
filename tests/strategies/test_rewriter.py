"""
Tests for the PlanRewriter class.
Tests cycle detection, depth caps, and idempotence.
"""

from unittest.mock import Mock
from proofengine.orchestrator.rewriter import PlanRewriter, CycleDetector
from proofengine.orchestrator.checker import BasicChecker
from proofengine.orchestrator.strategy_api import (
    Strategy,
    StrategyContext,
    RewritePlan,
    RewriteOperation,
)


class TestCycleDetector:
    """Test cycle detection functionality."""

    def test_no_cycle_detection(self):
        """Test that normal plans don't trigger cycle detection."""
        detector = CycleDetector()

        plan1 = {"steps": [{"id": "step1", "operator": "Meet"}]}
        plan2 = {"steps": [{"id": "step2", "operator": "Refute"}]}

        detector.add_plan_hash(plan1)
        assert not detector.has_cycle(plan2)

    def test_cycle_detection(self):
        """Test that identical plans trigger cycle detection."""
        detector = CycleDetector()

        plan = {"steps": [{"id": "step1", "operator": "Meet"}]}

        detector.add_plan_hash(plan)
        assert detector.has_cycle(plan)

    def test_hash_consistency(self):
        """Test that plan hashes are consistent."""
        detector = CycleDetector()

        plan1 = {"steps": [{"id": "step1", "operator": "Meet"}]}
        plan2 = {"steps": [{"id": "step1", "operator": "Meet"}]}

        hash1 = detector.add_plan_hash(plan1)
        hash2 = detector._compute_plan_hash(plan2)

        assert hash1 == hash2


class TestPlanRewriter:
    """Test plan rewriting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = BasicChecker()
        self.rewriter = PlanRewriter(self.checker)
        # Reset cycle detector for each test
        self.rewriter.cycle_detector = CycleDetector()
        self.mock_strategy = Mock(spec=Strategy)
        self.mock_strategy.id = "test_strategy"
        self.mock_strategy.guards = Mock()
        self.mock_strategy.guards.max_depth = 2
        self.mock_strategy.guards.max_rewrites_per_fr = 1
        self.mock_strategy.guards.stop_if_plan_grows = False
        self.mock_strategy.guards.max_plan_size_increase = 2
        self.mock_strategy.expected_outcomes = ["pass_or_block"]
        self.mock_strategy.estimate_success_probability.return_value = 0.8

    def test_apply_strategy_success(self):
        """Test successful strategy application."""
        # Setup
        plan = {"steps": [{"id": "step1", "operator": "Meet"}], "goal": "Test goal"}

        context = StrategyContext(
            failreason="contract.ambiguous_spec",
            operator="Generalize",
            plan=plan,
            current_step={"id": "step1", "operator": "Meet"},
            history=[],
            budgets={"time_ms": 1000, "audit_cost": 10.0},
        )

        self.mock_strategy.can_apply.return_value = True
        self.mock_strategy.create_rewrite_plan.return_value = RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:step1",
            steps=[{"id": "new_step", "operator": "Specialize"}],
        )

        # Execute
        result = self.rewriter.apply_strategy(self.mock_strategy, plan, context)

        # Verify
        assert result.success
        assert result.new_plan is not None
        assert len(result.new_plan["steps"]) == 2
        assert result.two_cell is not None

    def test_apply_strategy_cannot_apply(self):
        """Test strategy application when strategy cannot be applied."""
        # Setup
        plan = {"steps": []}
        context = StrategyContext(
            failreason="test_failure",
            operator="Meet",
            plan=plan,
            current_step={},
            history=[],
            budgets={},
        )

        self.mock_strategy.can_apply.return_value = False

        # Execute
        result = self.rewriter.apply_strategy(self.mock_strategy, plan, context)

        # Verify
        assert not result.success
        assert "cannot be applied" in result.error

    def test_apply_strategy_depth_limit(self):
        """Test strategy application with depth limit exceeded."""
        # Setup
        plan = {"steps": []}
        context = StrategyContext(
            failreason="test_failure",
            operator="Meet",
            plan=plan,
            current_step={},
            history=["rewrite", "rewrite", "rewrite"],  # 3 rewrites
            budgets={},
            depth=3,  # Exceeds max_depth=2
        )

        self.mock_strategy.guards.max_depth = 2
        self.mock_strategy.can_apply.return_value = True

        # Execute
        result = self.rewriter.apply_strategy(self.mock_strategy, plan, context)

        # Verify
        assert not result.success
        assert "Depth limit exceeded" in result.error

    def test_apply_strategy_cycle_detection(self):
        """Test strategy application with cycle detection."""
        # Setup
        plan = {"steps": [{"id": "step1", "operator": "Meet"}]}
        context = StrategyContext(
            failreason="test_failure",
            operator="Meet",
            plan=plan,
            current_step={"id": "step1", "operator": "Meet"},
            history=[],
            budgets={},
        )

        # Add the same plan to cycle detector
        self.rewriter.cycle_detector.add_plan_hash(plan)

        self.mock_strategy.can_apply.return_value = True
        self.mock_strategy.create_rewrite_plan.return_value = RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:step1",
            steps=[{"id": "new_step", "operator": "Specialize"}],
        )

        # Execute
        result = self.rewriter.apply_strategy(self.mock_strategy, plan, context)

        # Verify
        assert not result.success
        assert result.cycle_detected
        assert "Cycle detected" in result.error

    def test_apply_insert_operation(self):
        """Test insert operation."""
        plan = {
            "steps": [
                {"id": "step1", "operator": "Meet"},
                {"id": "step2", "operator": "Refute"},
            ]
        }

        rewrite_plan = RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:step2",
            steps=[{"id": "new_step", "operator": "Specialize"}],
        )

        context = StrategyContext(
            failreason="test",
            operator="Meet",
            plan=plan,
            current_step={},
            history=[],
            budgets={},
        )

        result = self.rewriter._apply_rewrite_plan(plan, rewrite_plan, context)

        assert len(result["steps"]) == 3
        assert result["steps"][1]["id"] == "new_step"

    def test_apply_replace_operation(self):
        """Test replace operation."""
        plan = {
            "steps": [
                {"id": "step1", "operator": "Meet"},
                {"id": "step2", "operator": "Refute"},
            ]
        }

        rewrite_plan = RewritePlan(
            operation=RewriteOperation.REPLACE,
            at="step2",
            with_step={"id": "step2", "operator": "Specialize"},
        )

        context = StrategyContext(
            failreason="test",
            operator="Meet",
            plan=plan,
            current_step={},
            history=[],
            budgets={},
        )

        result = self.rewriter._apply_rewrite_plan(plan, rewrite_plan, context)

        assert len(result["steps"]) == 2
        assert result["steps"][1]["operator"] == "Specialize"

    def test_apply_params_patch_operation(self):
        """Test params patch operation."""
        plan = {
            "steps": [
                {"id": "step1", "operator": "Meet", "params": {"confidence": 0.8}}
            ]
        }

        rewrite_plan = RewritePlan(
            operation=RewriteOperation.PARAMS_PATCH,
            at="step1",
            params_patch={"confidence": 0.9, "new_param": "value"},
        )

        context = StrategyContext(
            failreason="test",
            operator="Meet",
            plan=plan,
            current_step={},
            history=[],
            budgets={},
        )

        result = self.rewriter._apply_rewrite_plan(plan, rewrite_plan, context)

        assert result["steps"][0]["params"]["confidence"] == 0.9
        assert result["steps"][0]["params"]["new_param"] == "value"

    def test_depth_limit_exceeded(self):
        """Test that depth limit is properly enforced."""
        plan = {"steps": [{"id": "step1", "operator": "Meet"}], "goal": "Test goal"}

        # Create context with depth exceeding max_depth
        context = StrategyContext(
            failreason="contract.ambiguous_spec",
            operator="Generalize",
            plan=plan,
            current_step={"id": "step1", "operator": "Meet"},
            history=[],
            budgets={"time_ms": 1000, "audit_cost": 10.0},
            depth=3,  # Exceeds max_depth=2
        )

        self.mock_strategy.guards.max_depth = 2
        self.mock_strategy.can_apply.return_value = True

        result = self.rewriter.apply_strategy(self.mock_strategy, plan, context)

        assert not result.success
        assert "Depth limit exceeded" in result.error

    def test_plan_growth_guard_violation(self):
        """Test that plan growth guard is enforced."""
        plan = {"steps": [{"id": "step1", "operator": "Meet"}], "goal": "Test goal"}

        context = StrategyContext(
            failreason="contract.ambiguous_spec",
            operator="Generalize",
            plan=plan,
            current_step={"id": "step1", "operator": "Meet"},
            history=[],
            budgets={
                "time_ms": float("inf"),
                "audit_cost": float("inf"),
            },  # Disable budget constraints
        )

        self.mock_strategy.guards.stop_if_plan_grows = True
        self.mock_strategy.guards.max_plan_size_increase = 1
        self.mock_strategy.can_apply.return_value = True

        # Create a rewrite plan that adds too many steps
        self.mock_strategy.create_rewrite_plan.return_value = RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:step1",
            steps=[
                {"id": "new_step1", "operator": "Specialize"},
                {"id": "new_step2", "operator": "Specialize"},
                {
                    "id": "new_step3",
                    "operator": "Specialize",
                },  # This exceeds max_increase=1
            ],
        )

        result = self.rewriter.apply_strategy(self.mock_strategy, plan, context)

        assert not result.success
        assert "Plan growth guard violated" in result.error

    def test_budget_constraints_violation(self):
        """Test that budget constraints are enforced."""
        plan = {
            "steps": [{"id": "step1", "operator": "Meet"}],
            "goal": "Test goal",
            "budgets": {"time_ms": 1000, "audit_cost": 10.0},
        }

        context = StrategyContext(
            failreason="contract.ambiguous_spec",
            operator="Generalize",
            plan=plan,
            current_step={"id": "step1", "operator": "Meet"},
            history=[],
            budgets={"time_ms": 1000, "audit_cost": 10.0},
        )

        self.mock_strategy.can_apply.return_value = True
        self.mock_strategy.create_rewrite_plan.return_value = RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:step1",
            steps=[{"id": "new_step", "operator": "Specialize"}],
        )

        # Mock checker to return False for budget constraints
        self.checker.check_budget_constraints = Mock(return_value=False)

        result = self.rewriter.apply_strategy(self.mock_strategy, plan, context)

        assert not result.success
        assert "Budget constraints violated" in result.error

    def test_expected_outcomes_violation(self):
        """Test that expected outcomes are enforced."""
        plan = {"steps": [{"id": "step1", "operator": "Meet"}], "goal": "Test goal"}

        context = StrategyContext(
            failreason="contract.ambiguous_spec",
            operator="Generalize",
            plan=plan,
            current_step={"id": "step1", "operator": "Meet"},
            history=[],
            budgets={"time_ms": 1000, "audit_cost": 10.0},
        )

        self.mock_strategy.can_apply.return_value = True
        self.mock_strategy.create_rewrite_plan.return_value = RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:step1",
            steps=[{"id": "new_step", "operator": "Specialize"}],
        )

        # Mock checker to return False for expected outcomes
        self.checker.check_expected_outcomes = Mock(return_value=False)

        result = self.rewriter.apply_strategy(self.mock_strategy, plan, context)

        assert not result.success
        assert "Expected outcomes not met" in result.error

    def test_cycle_detection_prevents_infinite_loops(self):
        """Test that cycle detection prevents infinite loops."""
        plan = {"steps": [{"id": "step1", "operator": "Meet"}], "goal": "Test goal"}

        context = StrategyContext(
            failreason="contract.ambiguous_spec",
            operator="Generalize",
            plan=plan,
            current_step={"id": "step1", "operator": "Meet"},
            history=[],
            budgets={"time_ms": 1000, "audit_cost": 10.0},
        )

        # Add the same plan to cycle detector to simulate a cycle
        self.rewriter.cycle_detector.add_plan_hash(plan)

        self.mock_strategy.can_apply.return_value = True
        self.mock_strategy.create_rewrite_plan.return_value = RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:step1",
            steps=[{"id": "new_step", "operator": "Specialize"}],
        )

        result = self.rewriter.apply_strategy(self.mock_strategy, plan, context)

        assert not result.success
        assert result.cycle_detected
        assert "Cycle detected" in result.error
