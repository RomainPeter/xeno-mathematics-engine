"""
Tests for active gated mode execution.

Tests gates, rollback logic, budget constraints, and strategy application.
"""

from unittest.mock import Mock
from proofengine.orchestrator.modes import TwoCategoryOrchestrator, ActiveResult
from proofengine.orchestrator.strategy_api import (
    StrategyContext,
    StrategyRegistry,
    Guards,
)
from proofengine.orchestrator.rewriter import PlanRewriter
from proofengine.orchestrator.selector import StrategySelector, SelectionResult


class TestActiveGatedMode:
    """Test active gated mode functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock components
        self.mock_registry = Mock(spec=StrategyRegistry)
        self.mock_rewriter = Mock(spec=PlanRewriter)
        self.mock_selector = Mock(spec=StrategySelector)

        # Create orchestrator
        self.orchestrator = TwoCategoryOrchestrator(
            strategy_registry=self.mock_registry,
            rewriter=self.mock_rewriter,
            selector=self.mock_selector,
        )

        # Mock strategy
        self.mock_strategy = Mock()
        self.mock_strategy.id = "test_strategy"
        self.mock_strategy.guards = Guards(max_depth=2, max_rewrites_per_fr=1)

        # Mock context
        self.context = StrategyContext(
            failreason="contract.ambiguous_spec",
            operator="Generalize",
            plan={
                "steps": [{"id": "step1", "operator": "Meet"}],
                "goal": "Test goal",
                "budgets": {"time_ms": 1000, "audit_cost": 5.0},
            },
            current_step={"id": "step1", "operator": "Meet"},
            history=[],
            budgets={"time_ms": 2000, "audit_cost": 10.0},
            depth=0,
        )

    def test_basic_gates_pass(self):
        """Test basic gates when all conditions pass."""
        result = self.orchestrator._check_basic_gates(self.context, max_depth=2)
        assert result is True

    def test_basic_gates_depth_limit(self):
        """Test basic gates when depth limit exceeded."""
        self.context.depth = 3
        result = self.orchestrator._check_basic_gates(self.context, max_depth=2)
        assert result is False

    def test_basic_gates_time_budget_exceeded(self):
        """Test basic gates when time budget exceeded."""
        self.context.plan["budgets"]["time_ms"] = 3000  # Exceeds max_time=2000
        result = self.orchestrator._check_basic_gates(self.context, max_depth=2)
        assert result is False

    def test_basic_gates_cost_budget_exceeded(self):
        """Test basic gates when cost budget exceeded."""
        self.context.plan["budgets"]["audit_cost"] = 15.0  # Exceeds max_cost=10.0
        result = self.orchestrator._check_basic_gates(self.context, max_depth=2)
        assert result is False

    def test_basic_gates_cycle_detection(self):
        """Test basic gates with cycle detection."""
        # Simulate long history (potential cycle)
        self.context.history = [{"step": i} for i in range(15)]
        result = self.orchestrator._check_basic_gates(self.context, max_depth=2)
        assert result is False

    def test_selection_gates_pass(self):
        """Test selection gates when all conditions pass."""
        selection = SelectionResult(
            strategy_id="test_strategy",
            score=0.8,
            confidence=0.9,
            reason="Good fit",
            expected_gain=0.7,
            risk_assessment="low",
            alternatives=[],
            reasoning={},
            metadata={},
        )

        result = self.orchestrator._check_selection_gates(selection, 0.6, 0.1)
        assert result is True

    def test_selection_gates_confidence_too_low(self):
        """Test selection gates when confidence too low."""
        selection = SelectionResult(
            strategy_id="test_strategy",
            score=0.8,
            confidence=0.5,  # Below threshold
            reason="Good fit",
            expected_gain=0.7,
            risk_assessment="low",
            alternatives=[],
            reasoning={},
            metadata={},
        )

        result = self.orchestrator._check_selection_gates(selection, 0.6, 0.1)
        assert result is False

    def test_selection_gates_expected_gain_too_low(self):
        """Test selection gates when expected gain too low."""
        selection = SelectionResult(
            strategy_id="test_strategy",
            score=0.8,
            confidence=0.9,
            reason="Good fit",
            expected_gain=0.05,  # Below threshold
            risk_assessment="low",
            alternatives=[],
            reasoning={},
            metadata={},
        )

        result = self.orchestrator._check_selection_gates(selection, 0.6, 0.1)
        assert result is False

    def test_selection_gates_high_risk(self):
        """Test selection gates when risk is high."""
        selection = SelectionResult(
            strategy_id="test_strategy",
            score=0.8,
            confidence=0.9,
            reason="Good fit",
            expected_gain=0.7,
            risk_assessment="high",  # High risk
            alternatives=[],
            reasoning={},
            metadata={},
        )

        result = self.orchestrator._check_selection_gates(selection, 0.6, 0.1)
        assert result is False

    def test_track_strategy_failure(self):
        """Test strategy failure tracking."""
        strategy_id = "test_strategy"

        # First failure
        self.orchestrator._track_strategy_failure(strategy_id)
        assert self.orchestrator.failure_count[strategy_id] == 1
        assert strategy_id not in self.orchestrator.disabled_strategies

        # Second failure (should disable)
        self.orchestrator._track_strategy_failure(strategy_id)
        assert self.orchestrator.failure_count[strategy_id] == 2
        assert strategy_id in self.orchestrator.disabled_strategies

    def test_track_strategy_success(self):
        """Test strategy success tracking."""
        strategy_id = "test_strategy"

        # Set up failure state
        self.orchestrator.failure_count[strategy_id] = 1
        self.orchestrator.disabled_strategies.add(strategy_id)

        # Track success
        self.orchestrator._track_strategy_success(strategy_id)

        assert strategy_id not in self.orchestrator.failure_count
        assert strategy_id not in self.orchestrator.disabled_strategies

    def test_execute_active_gated_mode_success(self):
        """Test successful active gated mode execution."""
        # Mock successful selection
        selection_result = SelectionResult(
            strategy_id="test_strategy",
            score=0.8,
            confidence=0.9,
            reason="Good fit",
            expected_gain=0.7,
            risk_assessment="low",
            alternatives=[],
            reasoning={},
            metadata={},
        )

        # Mock successful rewrite
        rewrite_result = Mock()
        rewrite_result.success = True
        rewrite_result.new_plan = {"steps": [{"id": "new_step"}]}
        rewrite_result.two_cell = {"id": "two_cell_1"}

        # Configure mocks
        self.mock_registry.get_by_failreason.return_value = [self.mock_strategy]
        self.mock_selector.select_strategy.return_value = selection_result
        self.mock_rewriter.apply_strategy.return_value = rewrite_result

        # Execute
        result = self.orchestrator.execute_active_gated_mode(self.context)

        assert isinstance(result, ActiveResult)
        assert result.success is True
        assert result.applied_strategy == "test_strategy"
        assert result.new_plan == {"steps": [{"id": "new_step"}]}
        assert result.two_cell == {"id": "two_cell_1"}
        assert result.confidence == 0.9

    def test_execute_active_gated_mode_basic_gates_fail(self):
        """Test active mode when basic gates fail."""
        # Set up context that fails basic gates
        self.context.depth = 3  # Exceeds max_depth=2

        result = self.orchestrator.execute_active_gated_mode(self.context)

        assert isinstance(result, ActiveResult)
        assert result.success is False
        assert "Basic gates failed" in result.error

    def test_execute_active_gated_mode_no_strategies(self):
        """Test active mode when no strategies available."""
        self.mock_registry.get_by_failreason.return_value = []

        result = self.orchestrator.execute_active_gated_mode(self.context)

        assert isinstance(result, ActiveResult)
        assert result.success is False
        assert "No strategies available" in result.error

    def test_execute_active_gated_mode_selection_fails(self):
        """Test active mode when strategy selection fails."""
        self.mock_registry.get_by_failreason.return_value = [self.mock_strategy]
        self.mock_selector.select_strategy.side_effect = Exception("Selection failed")

        result = self.orchestrator.execute_active_gated_mode(self.context)

        assert isinstance(result, ActiveResult)
        assert result.success is False
        assert "Strategy selection failed" in result.error

    def test_execute_active_gated_mode_selection_gates_fail(self):
        """Test active mode when selection gates fail."""
        # Mock selection with low confidence
        selection_result = SelectionResult(
            strategy_id="test_strategy",
            score=0.8,
            confidence=0.5,  # Below threshold
            reason="Good fit",
            expected_gain=0.7,
            risk_assessment="low",
            alternatives=[],
            reasoning={},
            metadata={},
        )

        self.mock_registry.get_by_failreason.return_value = [self.mock_strategy]
        self.mock_selector.select_strategy.return_value = selection_result

        result = self.orchestrator.execute_active_gated_mode(self.context)

        assert isinstance(result, ActiveResult)
        assert result.success is False
        assert "Selection gates failed" in result.error

    def test_execute_active_gated_mode_strategy_not_found(self):
        """Test active mode when selected strategy not found."""
        selection_result = SelectionResult(
            strategy_id="nonexistent_strategy",
            score=0.8,
            confidence=0.9,
            reason="Good fit",
            expected_gain=0.7,
            risk_assessment="low",
            alternatives=[],
            reasoning={},
            metadata={},
        )

        self.mock_registry.get_by_failreason.return_value = [self.mock_strategy]
        self.mock_selector.select_strategy.return_value = selection_result

        result = self.orchestrator.execute_active_gated_mode(self.context)

        assert isinstance(result, ActiveResult)
        assert result.success is False
        assert "not found" in result.error

    def test_execute_active_gated_mode_rewrite_fails(self):
        """Test active mode when strategy application fails."""
        selection_result = SelectionResult(
            strategy_id="test_strategy",
            score=0.8,
            confidence=0.9,
            reason="Good fit",
            expected_gain=0.7,
            risk_assessment="low",
            alternatives=[],
            reasoning={},
            metadata={},
        )

        # Mock failed rewrite
        rewrite_result = Mock()
        rewrite_result.success = False
        rewrite_result.error = "Rewrite failed"

        self.mock_registry.get_by_failreason.return_value = [self.mock_strategy]
        self.mock_selector.select_strategy.return_value = selection_result
        self.mock_rewriter.apply_strategy.return_value = rewrite_result

        result = self.orchestrator.execute_active_gated_mode(self.context)

        assert isinstance(result, ActiveResult)
        assert result.success is False
        assert result.error == "Rewrite failed"
        assert result.selection_result == selection_result

    def test_execute_active_gated_mode_disabled_strategies(self):
        """Test active mode with disabled strategies."""
        # Disable the strategy
        self.orchestrator.disabled_strategies.add("test_strategy")

        self.mock_registry.get_by_failreason.return_value = [self.mock_strategy]

        result = self.orchestrator.execute_active_gated_mode(self.context)

        assert isinstance(result, ActiveResult)
        assert result.success is False
        assert "No strategies available" in result.error

    def test_rollback_mechanism(self):
        """Test rollback mechanism after consecutive failures."""
        strategy_id = "test_strategy"

        # First failure
        self.orchestrator._track_strategy_failure(strategy_id)
        assert strategy_id not in self.orchestrator.disabled_strategies

        # Second failure (triggers rollback)
        self.orchestrator._track_strategy_failure(strategy_id)
        assert strategy_id in self.orchestrator.disabled_strategies

        # Strategy should be excluded from selection
        self.mock_registry.get_by_failreason.return_value = [self.mock_strategy]
        result = self.orchestrator.execute_active_gated_mode(self.context)
        assert result.success is False

    def test_re_enable_after_success(self):
        """Test strategy re-enabling after success."""
        strategy_id = "test_strategy"

        # Disable strategy
        self.orchestrator.disabled_strategies.add(strategy_id)
        self.orchestrator.failure_count[strategy_id] = 2

        # Track success
        self.orchestrator._track_strategy_success(strategy_id)

        # Strategy should be re-enabled
        assert strategy_id not in self.orchestrator.disabled_strategies
        assert strategy_id not in self.orchestrator.failure_count

    def test_default_parameters(self):
        """Test default parameters for active gated mode."""
        # Set up mock registry to return empty list
        self.mock_registry.get_by_failreason.return_value = []

        # Should use default thresholds
        result = self.orchestrator.execute_active_gated_mode(self.context)

        # Should return failure due to no strategies
        assert not result.success
        assert "No strategies available" in result.error
        # Check that basic gates are called with default max_depth=2
        assert self.context.depth < 2  # Should pass basic gates
