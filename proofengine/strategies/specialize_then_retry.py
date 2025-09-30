"""
Specialize Then Retry Strategy.
Handles contract.ambiguous_spec failures by adding specialization step.
"""

from ..orchestrator.strategy_api import (
    Strategy,
    StrategyContext,
    RewritePlan,
    RewriteOperation,
)


class SpecializeThenRetryStrategy(Strategy):
    """Strategy for handling ambiguous specifications."""

    def __init__(self):
        super().__init__(
            id="specialize_then_retry",
            trigger_codes=["contract.ambiguous_spec"],
            expected_outcomes=["pass_or_block"],
        )

    def can_apply(self, context: StrategyContext) -> bool:
        """Check if strategy can be applied."""
        return (
            context.failreason == "contract.ambiguous_spec"
            and context.operator == "Generalize"
            and len(context.plan.get("steps", [])) > 0
        )

    def create_rewrite_plan(self, context: StrategyContext) -> RewritePlan:
        """Create rewrite plan to add specialization step."""
        return RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:current",
            steps=[
                {
                    "id": f"specialize_{context.current_step.get('id', 'unknown')}",
                    "operator": "Specialize",
                    "params": {
                        "questions": [
                            "clarify: inputs",
                            "clarify: outputs",
                            "clarify: constraints",
                        ]
                    },
                    "expected": "Clarified specification",
                }
            ],
        )

    def estimate_success_probability(self, context: StrategyContext) -> float:
        """Estimate success probability."""
        # Higher probability if the step has unclear parameters
        params = context.current_step.get("params", {})
        if not params or len(params) < 2:
            return 0.8
        return 0.6
