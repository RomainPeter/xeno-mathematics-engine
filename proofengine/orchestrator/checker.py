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

        # Check plan size increase
        original_steps = len(original_plan.get("steps", []))
        new_steps = len(new_plan.get("steps", []))
        max_increase = budgets.get("max_plan_size_increase", 2)

        if new_steps > original_steps + max_increase:
            return False

        return True

    def check_expected_outcomes(
        self, strategy: Strategy, context: StrategyContext
    ) -> bool:
        """Check if expected outcomes are plausible."""
        # For now, always return True - in a full implementation,
        # this would check if the expected outcomes are realistic
        # given the current context and strategy
        return True
