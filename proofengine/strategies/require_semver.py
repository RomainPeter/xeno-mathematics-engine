"""
Require Semver Strategy.
Handles api.semver_missing failures by blocking or inserting semver step.
"""

from ..orchestrator.strategy_api import (RewriteOperation, RewritePlan,
                                         Strategy, StrategyContext)


class RequireSemverStrategy(Strategy):
    """Strategy for handling missing semantic versioning."""

    def __init__(self):
        super().__init__(
            id="require_semver",
            trigger_codes=["api.semver_missing", "policy.semver_violation"],
            expected_outcomes=["must_block", "policy_clean"],
        )

    def can_apply(self, context: StrategyContext) -> bool:
        """Check if strategy can be applied."""
        return context.failreason in [
            "api.semver_missing",
            "policy.semver_violation",
        ] and context.operator in ["Normalize", "Verify"]

    def create_rewrite_plan(self, context: StrategyContext) -> RewritePlan:
        """Create rewrite plan to add semver normalization."""
        current_step_id = context.current_step.get("id", "step1")
        return RewritePlan(
            operation=RewriteOperation.INSERT,
            at=f"before:{current_step_id}",
            steps=[
                {
                    "id": f"normalize_semver_{current_step_id}",
                    "operator": "Normalize",
                    "params": {
                        "target": "semver",
                        "version_scheme": "semantic",
                        "bump_type": "patch",
                        "require_changelog": True,
                    },
                    "expected": "Semantic versioning applied",
                }
            ],
        )

    def estimate_success_probability(self, context: StrategyContext) -> float:
        """Estimate success probability."""
        # Check if semver is already present in the plan
        existing_semver = any(
            step.get("operator") == "Normalize"
            and "semver" in step.get("params", {}).get("target", "")
            for step in context.plan.get("steps", [])
        )

        if existing_semver:
            return 0.3  # Low probability if semver already exists
        return 0.9  # High probability if no semver exists
