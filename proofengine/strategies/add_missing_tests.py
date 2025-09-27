"""
Add Missing Tests Strategy.
Handles coverage.missing_tests failures by inserting test step before Verify.
"""

from ..orchestrator.strategy_api import (
    Strategy,
    StrategyContext,
    RewritePlan,
    RewriteOperation,
)


class AddMissingTestsStrategy(Strategy):
    """Strategy for handling missing test coverage."""

    def __init__(self):
        super().__init__(
            id="add_missing_tests",
            trigger_codes=[
                "coverage.missing_tests",
                "coverage.insufficient_line_coverage",
            ],
            expected_outcomes=["coverage_increase"],
        )

    def can_apply(self, context: StrategyContext) -> bool:
        """Check if strategy can be applied."""
        return context.failreason in [
            "coverage.missing_tests",
            "coverage.insufficient_line_coverage",
        ] and "Verify" in [
            step.get("operator") for step in context.plan.get("steps", [])
        ]

    def create_rewrite_plan(self, context: StrategyContext) -> RewritePlan:
        """Create rewrite plan to add test step before Verify."""
        return RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:Verify",
            steps=[
                {
                    "id": f"test_coverage_{context.current_step.get('id', 'unknown')}",
                    "operator": "Meet",
                    "params": {
                        "hypothesis": "Test coverage is sufficient",
                        "evidence_types": ["test", "coverage_report"],
                        "min_coverage": 0.8,
                    },
                    "expected": "Coverage requirements met",
                }
            ],
        )

    def estimate_success_probability(self, context: StrategyContext) -> float:
        """Estimate success probability."""
        # Check if there are existing tests in the plan
        existing_tests = sum(
            1
            for step in context.plan.get("steps", [])
            if step.get("operator") == "Meet"
            and "test" in step.get("params", {}).get("evidence_types", [])
        )

        if existing_tests == 0:
            return 0.9  # High probability if no tests exist
        return 0.7  # Medium probability if some tests exist
