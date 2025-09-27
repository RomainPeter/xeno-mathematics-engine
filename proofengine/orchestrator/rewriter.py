"""
Rewriter for applying 2-category transformations.
Handles cycle detection, depth limits, and plan rewriting.
"""

import hashlib
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .strategy_api import Strategy, RewritePlan, StrategyContext, Checker


@dataclass
class RewriteResult:
    """Result of a rewrite operation."""

    success: bool
    new_plan: Optional[Dict[str, Any]] = None
    two_cell: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    depth: int = 0
    cycle_detected: bool = False


class CycleDetector:
    """Detects cycles in plan rewriting."""

    def __init__(self):
        self._plan_hashes: set = set()

    def add_plan_hash(self, plan: Dict[str, Any]) -> str:
        """Add a plan and return its hash."""
        plan_hash = self._compute_plan_hash(plan)
        self._plan_hashes.add(plan_hash)
        return plan_hash

    def has_cycle(self, plan: Dict[str, Any]) -> bool:
        """Check if plan creates a cycle."""
        plan_hash = self._compute_plan_hash(plan)
        return plan_hash in self._plan_hashes

    def _compute_plan_hash(self, plan: Dict[str, Any]) -> str:
        """Compute hash of plan structure (ignoring timestamps)."""
        # Create a normalized version for hashing
        normalized = {"steps": plan.get("steps", []), "goal": plan.get("goal", "")}
        # Sort steps by ID for consistent hashing
        if "steps" in normalized:
            normalized["steps"] = sorted(
                normalized["steps"], key=lambda x: x.get("id", "")
            )

        plan_str = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(plan_str.encode()).hexdigest()


class PlanRewriter:
    """Rewrites plans using strategies."""

    def __init__(self, checker: Checker):
        self.checker = checker
        self.cycle_detector = CycleDetector()

    def apply_strategy(
        self, strategy: Strategy, plan: Dict[str, Any], context: StrategyContext
    ) -> RewriteResult:
        """Apply a strategy to rewrite a plan."""

        # Check if strategy can be applied
        if not strategy.can_apply(context):
            return RewriteResult(
                success=False,
                error=f"Strategy {strategy.id} cannot be applied to context",
            )

        # Check depth limits using explicit depth counter
        if not self.checker.check_depth_limit(context.depth, strategy.guards.max_depth):
            return RewriteResult(
                success=False,
                error=f"Depth limit exceeded: {context.depth} > {strategy.guards.max_depth}",
            )

        # Check for cycles BEFORE adding to detector
        if self.cycle_detector.has_cycle(plan):
            return RewriteResult(
                success=False, error="Cycle detected in plan", cycle_detected=True
            )

        # Add current plan to cycle detector AFTER checking for cycles
        self.cycle_detector.add_plan_hash(plan)

        # Create rewrite plan
        try:
            rewrite_plan = strategy.create_rewrite_plan(context)
        except Exception as e:
            return RewriteResult(
                success=False, error=f"Failed to create rewrite plan: {str(e)}"
            )

        # Apply the rewrite
        try:
            new_plan = self._apply_rewrite_plan(plan, rewrite_plan, context)
        except Exception as e:
            return RewriteResult(
                success=False, error=f"Failed to apply rewrite: {str(e)}"
            )

        # Check budget constraints
        if not self.checker.check_budget_constraints(plan, new_plan, context.budgets):
            return RewriteResult(success=False, error="Budget constraints violated")

        # Check plan growth guard
        if not self.checker.check_plan_growth_guard(plan, new_plan, strategy):
            return RewriteResult(success=False, error="Plan growth guard violated")

        # Check expected outcomes
        if not self.checker.check_expected_outcomes(strategy, context):
            return RewriteResult(success=False, error="Expected outcomes not met")

        # Create two_cell record
        two_cell = self._create_two_cell(strategy, rewrite_plan, context, new_plan)

        return RewriteResult(
            success=True, new_plan=new_plan, two_cell=two_cell, depth=context.depth + 1
        )

    def _apply_rewrite_plan(
        self, plan: Dict[str, Any], rewrite_plan: RewritePlan, context: StrategyContext
    ) -> Dict[str, Any]:
        """Apply a rewrite plan to a plan."""
        new_plan = plan.copy()
        new_plan["steps"] = plan["steps"].copy()

        if rewrite_plan.operation.value == "insert":
            self._apply_insert(new_plan, rewrite_plan)
        elif rewrite_plan.operation.value == "replace":
            self._apply_replace(new_plan, rewrite_plan)
        elif rewrite_plan.operation.value == "branch":
            self._apply_branch(new_plan, rewrite_plan)
        elif rewrite_plan.operation.value == "params_patch":
            self._apply_params_patch(new_plan, rewrite_plan)

        # Update timestamps
        new_plan["updated_at"] = datetime.now().isoformat()

        return new_plan

    def _apply_insert(self, plan: Dict[str, Any], rewrite_plan: RewritePlan) -> None:
        """Apply insert operation."""
        if not rewrite_plan.steps:
            return

        at_pos = self._find_step_position(plan, rewrite_plan.at)
        if at_pos is None:
            raise ValueError(f"Step position not found: {rewrite_plan.at}")

        # Insert steps at the specified position
        for i, step in enumerate(rewrite_plan.steps):
            plan["steps"].insert(at_pos + i, step)

    def _apply_replace(self, plan: Dict[str, Any], rewrite_plan: RewritePlan) -> None:
        """Apply replace operation."""
        if not rewrite_plan.with_step:
            return

        step_pos = self._find_step_position(plan, rewrite_plan.at)
        if step_pos is None:
            raise ValueError(f"Step not found: {rewrite_plan.at}")

        plan["steps"][step_pos] = rewrite_plan.with_step

    def _apply_branch(self, plan: Dict[str, Any], rewrite_plan: RewritePlan) -> None:
        """Apply branch operation.

        NOTE: This is a simplified implementation that only handles the first branch.
        A full implementation would need to:
        1. Evaluate branch conditions
        2. Handle multiple branches with proper control flow
        3. Manage branch state and execution context

        For now, we raise an exception to prevent silent failures.
        """
        if not rewrite_plan.branches:
            return

        # Branching is not fully implemented - raise explicit exception
        raise NotImplementedError(
            "Branch operation is not fully implemented. "
            "This would require conditional execution logic and proper branch management. "
            "Consider using INSERT or REPLACE operations instead."
        )

    def _apply_params_patch(
        self, plan: Dict[str, Any], rewrite_plan: RewritePlan
    ) -> None:
        """Apply params patch operation."""
        if not rewrite_plan.params_patch:
            return

        step_pos = self._find_step_position(plan, rewrite_plan.at)
        if step_pos is None:
            raise ValueError(f"Step not found: {rewrite_plan.at}")

        # Patch parameters
        if "params" not in plan["steps"][step_pos]:
            plan["steps"][step_pos]["params"] = {}
        plan["steps"][step_pos]["params"].update(rewrite_plan.params_patch)

    def _find_step_position(self, plan: Dict[str, Any], step_ref: str) -> Optional[int]:
        """Find the position of a step in the plan."""
        if step_ref.startswith("before:"):
            step_id = step_ref[7:]  # Remove "before:" prefix
            for i, step in enumerate(plan["steps"]):
                if step.get("id") == step_id:
                    return i
        elif step_ref.startswith("after:"):
            step_id = step_ref[6:]  # Remove "after:" prefix
            for i, step in enumerate(plan["steps"]):
                if step.get("id") == step_id:
                    return i + 1
        else:
            # Direct step ID
            for i, step in enumerate(plan["steps"]):
                if step.get("id") == step_ref:
                    return i
        return None

    def _create_two_cell(
        self,
        strategy: Strategy,
        rewrite_plan: RewritePlan,
        context: StrategyContext,
        new_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a two_cell record."""
        return {
            "version": "0.2.0",
            "id": f"two_cell_{strategy.id}_{int(datetime.now().timestamp())}",
            "from_op": context.operator,
            "to_choreo": [
                step.get("operator", "") for step in rewrite_plan.steps or []
            ],
            "trigger": {
                "failreason": context.failreason,
                "operator": context.operator,
                "context": context.current_step,
            },
            "pre_invariants": [],
            "post_invariants": [],
            "budgets": {
                "time_ms": context.budgets.get("time_ms", 0),
                "audit_cost": context.budgets.get("audit_cost", 0.0),
                "max_depth": strategy.guards.max_depth,
                "max_rewrites_per_fr": strategy.guards.max_rewrites_per_fr,
            },
            "evidence": {
                "prompt_hash": hashlib.sha256(str(context).encode()).hexdigest(),
                "model": "deterministic",
                "n": 1,
                "votes": 1,
                "latency_ms": 0,
            },
            "decision_signature": "",
            "prev_hash": "",
            "entry_hash": "",
            "created_at": datetime.now().isoformat(),
        }
