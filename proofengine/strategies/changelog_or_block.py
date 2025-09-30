"""
Changelog Or Block Strategy.
Handles api.changelog_missing failures by requiring changelog or blocking.
"""

from ..orchestrator.strategy_api import (
    Strategy,
    StrategyContext,
    RewritePlan,
    RewriteOperation,
)


class ChangelogOrBlockStrategy(Strategy):
    """Strategy for handling missing changelog."""

    def __init__(self):
        super().__init__(
            id="changelog_or_block",
            trigger_codes=["api.changelog_missing", "policy.changelog_missing"],
            expected_outcomes=["must_block", "policy_clean"],
        )

    def can_apply(self, context: StrategyContext) -> bool:
        """Check if strategy can be applied."""
        return context.failreason in [
            "api.changelog_missing",
            "policy.changelog_missing",
        ] and context.operator in ["Normalize", "Verify"]

    def create_rewrite_plan(self, context: StrategyContext) -> RewritePlan:
        """Create rewrite plan to add changelog requirement."""
        return RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:current",
            steps=[
                {
                    "id": f"require_changelog_{context.current_step.get('id', 'unknown')}",
                    "operator": "Normalize",
                    "params": {
                        "target": "changelog",
                        "format": "keepachangelog",
                        "require_entry": True,
                        "block_on_missing": True,
                    },
                    "expected": "Changelog entry present",
                }
            ],
        )

    def estimate_success_probability(self, context: StrategyContext) -> float:
        """Estimate success probability."""
        # Check if changelog is already present in the plan
        existing_changelog = any(
            step.get("operator") == "Normalize"
            and "changelog" in step.get("params", {}).get("target", "")
            for step in context.plan.get("steps", [])
        )

        if existing_changelog:
            return 0.2  # Low probability if changelog already exists
        return 0.8  # High probability if no changelog exists
