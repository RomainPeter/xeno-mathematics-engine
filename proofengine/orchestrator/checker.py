"""
Checker implementation for 2-category transformations.
Provides concrete implementations of the Checker interface.
"""

from typing import Dict, List, Any
from .strategy_api import Checker, Strategy, StrategyContext


class BasicChecker(Checker):
    """Basic implementation of the Checker interface."""

    def check_cycle_detection(
        self, plan: Dict[str, Any], history: List[Dict[str, Any]]
    ) -> bool:
        """Check for cycles in the plan."""
        # Simple cycle detection based on step IDs
        step_ids = [step.get("id") for step in plan.get("steps", [])]
        unique_ids = set(step_ids)

        # If we have duplicate step IDs, it's a cycle
        if len(step_ids) != len(unique_ids):
            return False

        # Check for repeated patterns in history
        if len(history) > 3:
            recent_history = history[-3:]
            if len(set(str(h) for h in recent_history)) < len(recent_history):
                return False

        return True

    def check_depth_limit(self, depth: int, max_depth: int) -> bool:
        """Check if depth is within limits."""
        return depth <= max_depth

    def check_budget_constraints(
        self,
        original_plan: Dict[str, Any],
        new_plan: Dict[str, Any],
        budgets: Dict[str, Any],
    ) -> bool:
        """Check if budget constraints are respected."""
        # Check time budget
        new_time = new_plan.get("budgets", {}).get("time_ms", 0)
        max_time = budgets.get("time_ms", float("inf"))

        if new_time > max_time:
            return False

        # Check audit cost budget
        new_cost = new_plan.get("budgets", {}).get("audit_cost", 0.0)
        max_cost = budgets.get("audit_cost", float("inf"))

        if new_cost > max_cost:
            return False

        # Note: Plan size increase is now handled by check_plan_growth_guard
        # to avoid duplication and ensure consistent behavior

        return True

    def check_plan_growth_guard(
        self,
        original_plan: Dict[str, Any],
        new_plan: Dict[str, Any],
        strategy: Strategy,
    ) -> bool:
        """Check if plan growth respects the stop_if_plan_grows guard."""
        if not strategy.guards.stop_if_plan_grows:
            return True

        original_steps = len(original_plan.get("steps", []))
        new_steps = len(new_plan.get("steps", []))
        max_increase = strategy.guards.max_plan_size_increase

        return new_steps <= original_steps + max_increase

    def check_expected_outcomes(
        self, strategy: Strategy, context: StrategyContext
    ) -> bool:
        """Check if expected outcomes are plausible."""
        if not strategy.expected_outcomes:
            return True

        # Check if strategy can achieve its expected outcomes
        for outcome in strategy.expected_outcomes:
            if outcome == "must_block":
                # For blocking strategies, check if they have blocking mechanisms
                if not self._has_blocking_mechanism(strategy, context):
                    return False
            elif outcome == "must_pass":
                # For passing strategies, check if success probability is reasonable
                success_prob = strategy.estimate_success_probability(context)
                if success_prob < 0.5:  # Minimum threshold for "must_pass"
                    return False
            elif outcome == "coverage_increase":
                # For coverage strategies, check if they target coverage
                if not self._targets_coverage(strategy, context):
                    return False
            elif outcome == "policy_clean":
                # For policy strategies, check if they target policy compliance
                if not self._targets_policy_compliance(strategy, context):
                    return False

        return True

    def _has_blocking_mechanism(
        self, strategy: Strategy, context: StrategyContext
    ) -> bool:
        """Check if strategy has blocking mechanisms."""
        # Strategies that can block typically have "block" or "require" in their logic
        return (
            "block" in strategy.id.lower()
            or "require" in strategy.id.lower()
            or any("block" in outcome.lower() for outcome in strategy.expected_outcomes)
        )

    def _targets_coverage(self, strategy: Strategy, context: StrategyContext) -> bool:
        """Check if strategy targets coverage improvement."""
        return (
            "coverage" in strategy.id.lower()
            or "test" in strategy.id.lower()
            or context.failreason.startswith("coverage.")
        )

    def _targets_policy_compliance(
        self, strategy: Strategy, context: StrategyContext
    ) -> bool:
        """Check if strategy targets policy compliance."""
        return (
            "policy" in strategy.id.lower()
            or "semver" in strategy.id.lower()
            or "changelog" in strategy.id.lower()
            or context.failreason.startswith("policy.")
            or context.failreason.startswith("api.")
        )
