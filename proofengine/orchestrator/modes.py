"""
Execution modes for 2-category transformations.
Implements shadow mode and active gated mode.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from .strategy_api import StrategyContext, StrategySelector, StrategyRegistry
from .rewriter import PlanRewriter
from .selector import SelectionResult


class ExecutionMode(Enum):
    """Execution modes for 2-category transformations."""

    SHADOW = "shadow"
    ACTIVE_GATED = "active_gated"


@dataclass
class ShadowReport:
    """Report from shadow mode execution."""

    mode: str
    timestamp: str
    proposals: List[Dict[str, Any]]
    total_strategies_evaluated: int
    applicable_strategies: int
    success_rate: float


@dataclass
class ActiveResult:
    """Result from active mode execution."""

    success: bool
    applied_strategy: Optional[str] = None
    new_plan: Optional[Dict[str, Any]] = None
    two_cell: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    rationale: str = ""
    selection_result: Optional[SelectionResult] = None
    error: Optional[str] = None
    rollback_triggered: bool = False


class TwoCategoryOrchestrator:
    """Orchestrator for 2-category transformations."""

    def __init__(
        self,
        strategy_registry: StrategyRegistry,
        rewriter: PlanRewriter,
        selector: StrategySelector,
    ):
        self.strategy_registry = strategy_registry
        self.rewriter = rewriter
        self.selector = selector
        self.failure_count = {}  # Track consecutive failures per strategy
        self.disabled_strategies = set()  # Strategies disabled due to failures

    def execute_shadow_mode(self, context: StrategyContext) -> ShadowReport:
        """Execute in shadow mode - generate proposals without applying."""
        proposals = []
        applicable_strategies = 0
        total_strategies = 0

        # Get candidate strategies for the failreason
        candidates = self.strategy_registry.get_by_failreason(context.failreason)
        total_strategies = len(candidates)

        for strategy in candidates:
            if strategy.can_apply(context):
                applicable_strategies += 1

                # Create rewrite plan (but don't apply)
                try:
                    rewrite_plan = strategy.create_rewrite_plan(context)
                    success_prob = strategy.estimate_success_probability(context)

                    proposal = {
                        "strategy_id": strategy.id,
                        "failreason": context.failreason,
                        "operator": context.operator,
                        "rewrite_plan": {
                            "operation": rewrite_plan.operation.value,
                            "at": rewrite_plan.at,
                            "steps": rewrite_plan.steps,
                            "with_step": rewrite_plan.with_step,
                            "branches": rewrite_plan.branches,
                            "params_patch": rewrite_plan.params_patch,
                        },
                        "success_probability": success_prob,
                        "expected_outcomes": strategy.expected_outcomes,
                        "guards": {
                            "max_depth": strategy.guards.max_depth,
                            "max_rewrites_per_fr": strategy.guards.max_rewrites_per_fr,
                        },
                    }
                    proposals.append(proposal)
                except Exception as e:
                    # Log error but continue
                    print(f"Error creating proposal for {strategy.id}: {e}")

        success_rate = (
            applicable_strategies / total_strategies if total_strategies > 0 else 0.0
        )

        return ShadowReport(
            mode="shadow",
            timestamp=datetime.now().isoformat(),
            proposals=proposals,
            total_strategies_evaluated=total_strategies,
            applicable_strategies=applicable_strategies,
            success_rate=success_rate,
        )

    def execute_active_gated_mode(
        self,
        context: StrategyContext,
        confidence_threshold: float = 0.6,
        delta_v_threshold: float = 0.1,
        max_depth: int = 2,
    ) -> ActiveResult:
        """Execute in active gated mode with enhanced gates and rollback."""

        # Check basic gates
        if not self._check_basic_gates(context, max_depth):
            return ActiveResult(
                success=False, error="Basic gates failed (budget, depth, cycle)"
            )

        # Get candidate strategies (excluding disabled ones)
        candidates = self.strategy_registry.get_by_failreason(context.failreason)
        candidates = [s for s in candidates if s.id not in self.disabled_strategies]

        if not candidates:
            return ActiveResult(
                success=False,
                error=f"No strategies available for failreason: {context.failreason}",
            )

        # Select best strategy using LLM selector
        try:
            selection_result = self.selector.select_strategy(context, candidates)
        except Exception as e:
            return ActiveResult(success=False, error=f"Strategy selection failed: {e}")

        # Check selection gates
        if not self._check_selection_gates(
            selection_result, confidence_threshold, delta_v_threshold
        ):
            return ActiveResult(
                success=False,
                error=f"Selection gates failed: confidence={selection_result.confidence:.2f}, expected_gain={selection_result.expected_gain:.2f}",
            )

        # Find the selected strategy
        strategy = next(
            (s for s in candidates if s.id == selection_result.strategy_id), None
        )
        if not strategy:
            return ActiveResult(
                success=False,
                error=f"Selected strategy {selection_result.strategy_id} not found",
            )

        # Apply the strategy
        result = self.rewriter.apply_strategy(strategy, context.plan, context)

        if not result.success:
            # Track failure for rollback logic
            self._track_strategy_failure(strategy.id)
            return ActiveResult(
                success=False, error=result.error, selection_result=selection_result
            )

        # Track success (reset failure count)
        self._track_strategy_success(strategy.id)

        return ActiveResult(
            success=True,
            applied_strategy=strategy.id,
            new_plan=result.new_plan,
            two_cell=result.two_cell,
            confidence=selection_result.confidence,
            rationale=selection_result.reason,
            selection_result=selection_result,
        )

    def _check_basic_gates(self, context: StrategyContext, max_depth: int) -> bool:
        """Check basic gates: budget, depth, cycle."""

        # Check depth limit
        if context.depth >= max_depth:
            return False

        # Check budget constraints - use plan budgets as current, context budgets as limits
        plan_budgets = context.plan.get("budgets", {})
        current_time = plan_budgets.get("time_ms", 0)
        max_time = context.budgets.get("time_ms", float("inf"))
        if current_time > max_time:
            return False

        current_cost = plan_budgets.get("audit_cost", 0.0)
        max_cost = context.budgets.get("audit_cost", float("inf"))
        if current_cost > max_cost:
            return False

        # Check for cycles (simplified)
        if len(context.history) > 10:  # Simple cycle detection
            return False

        return True

    def _check_selection_gates(
        self,
        selection_result: SelectionResult,
        confidence_threshold: float,
        delta_v_threshold: float,
    ) -> bool:
        """Check selection-specific gates."""

        # Confidence threshold
        if selection_result.confidence < confidence_threshold:
            return False

        # Expected gain threshold
        if selection_result.expected_gain < delta_v_threshold:
            return False

        # Risk assessment
        if selection_result.risk_assessment == "high":
            return False

        return True

    def _track_strategy_failure(self, strategy_id: str) -> None:
        """Track strategy failure for rollback logic."""
        self.failure_count[strategy_id] = self.failure_count.get(strategy_id, 0) + 1

        # Disable strategy after 2 consecutive failures
        if self.failure_count[strategy_id] >= 2:
            self.disabled_strategies.add(strategy_id)
            print(f"Strategy {strategy_id} disabled due to consecutive failures")

    def _track_strategy_success(self, strategy_id: str) -> None:
        """Track strategy success (reset failure count)."""
        if strategy_id in self.failure_count:
            del self.failure_count[strategy_id]

        # Re-enable strategy if it was disabled
        if strategy_id in self.disabled_strategies:
            self.disabled_strategies.remove(strategy_id)
            print(f"Strategy {strategy_id} re-enabled after success")

    def save_shadow_report(self, report: ShadowReport, output_path: str) -> None:
        """Save shadow report to file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "mode": report.mode,
                    "timestamp": report.timestamp,
                    "proposals": report.proposals,
                    "total_strategies_evaluated": report.total_strategies_evaluated,
                    "applicable_strategies": report.applicable_strategies,
                    "success_rate": report.success_rate,
                },
                f,
                indent=2,
            )

    def save_two_cells(self, two_cells: List[Dict[str, Any]], output_path: str) -> None:
        """Save two_cells to JSONL file."""
        with open(output_path, "w", encoding="utf-8") as f:
            for two_cell in two_cells:
                f.write(json.dumps(two_cell) + "\n")

    def load_strategies_from_yaml(self, yaml_path: str) -> None:
        """Load strategies from YAML configuration."""
        # This would be implemented to load strategy definitions from YAML
        # For now, we'll implement this in the strategy implementations
        pass
