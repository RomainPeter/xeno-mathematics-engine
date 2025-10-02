"""
Retry With Hardening Strategy.
Handles nondet.flaky_test failures by fixing seed and rerunning.
"""

from ..orchestrator.strategy_api import RewriteOperation, RewritePlan, Strategy, StrategyContext


class RetryWithHardeningStrategy(Strategy):
    """Strategy for handling flaky/nondeterministic tests."""

    def __init__(self):
        super().__init__(
            id="retry_with_hardening",
            trigger_codes=[
                "nondet.flaky_test",
                "nondet.race_condition",
                "nondet.seed_dependent",
            ],
            expected_outcomes=["pass_or_block"],
        )

    def can_apply(self, context: StrategyContext) -> bool:
        """Check if strategy can be applied."""
        return context.failreason in [
            "nondet.flaky_test",
            "nondet.race_condition",
            "nondet.seed_dependent",
        ] and context.operator in ["Meet", "Verify"]

    def create_rewrite_plan(self, context: StrategyContext) -> RewritePlan:
        """Create rewrite plan to add hardening step."""
        return RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:current",
            steps=[
                {
                    "id": f"harden_{context.current_step.get('id', 'unknown')}",
                    "operator": "Normalize",
                    "params": {
                        "target": "test_environment",
                        "fix_seed": True,
                        "seed_value": 42,  # Fixed seed for reproducibility
                        "retry_count": 3,
                        "timeout_ms": 30000,
                    },
                    "expected": "Deterministic test execution",
                }
            ],
        )

    def estimate_success_probability(self, context: StrategyContext) -> float:
        """Estimate success probability."""
        # Check if hardening is already applied
        existing_hardening = any(
            step.get("operator") == "Normalize" and "fix_seed" in step.get("params", {})
            for step in context.plan.get("steps", [])
        )

        if existing_hardening:
            return 0.4  # Medium probability if hardening already exists
        return 0.9  # High probability if no hardening exists
