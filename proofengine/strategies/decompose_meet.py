"""
Decompose Meet Strategy.
Handles runner.test_failure on Meet(A∧B) by separating into A then B.
"""

from typing import Dict, List, Any
from ..orchestrator.strategy_api import (
    Strategy,
    StrategyContext,
    RewritePlan,
    RewriteOperation,
)


class DecomposeMeetStrategy(Strategy):
    """Strategy for decomposing complex Meet operations."""

    def __init__(self):
        super().__init__(
            id="decompose_meet",
            trigger_codes=["runner.test_failure", "runner.pytest_failure"],
            expected_outcomes=["pass_or_block"],
        )

    def can_apply(self, context: StrategyContext) -> bool:
        """Check if strategy can be applied."""
        return (
            context.failreason in ["runner.test_failure", "runner.pytest_failure"]
            and context.operator == "Meet"
            and self._has_complex_hypothesis(context.current_step)
        )

    def _has_complex_hypothesis(self, step: Dict[str, Any]) -> bool:
        """Check if step has complex hypothesis that can be decomposed."""
        params = step.get("params", {})
        hypothesis = params.get("hypothesis", "")

        # Look for conjunction patterns (A∧B, A AND B, etc.)
        conjunction_indicators = ["∧", "AND", "&", " and "]
        return any(indicator in hypothesis for indicator in conjunction_indicators)

    def create_rewrite_plan(self, context: StrategyContext) -> RewritePlan:
        """Create rewrite plan to decompose Meet operation."""
        params = context.current_step.get("params", {})
        hypothesis = params.get("hypothesis", "")

        # Simple decomposition - split on common conjunctions
        decomposed_hypotheses = self._decompose_hypothesis(hypothesis)

        steps = []
        for i, sub_hypothesis in enumerate(decomposed_hypotheses):
            steps.append(
                {
                    "id": f"meet_{i}_{context.current_step.get('id', 'unknown')}",
                    "operator": "Meet",
                    "params": {
                        "hypothesis": sub_hypothesis.strip(),
                        "evidence_types": params.get("evidence_types", []),
                        "min_confidence": params.get("min_confidence", 0.8),
                    },
                    "expected": f"Hypothesis {i+1} supported",
                }
            )

        return RewritePlan(
            operation=RewriteOperation.REPLACE,
            at=context.current_step.get("id", "unknown"),
            with_step={
                "id": f"decomposed_{context.current_step.get('id', 'unknown')}",
                "operator": "Meet",
                "params": {
                    "hypothesis": "Decomposed hypotheses",
                    "sub_hypotheses": decomposed_hypotheses,
                    "evidence_types": params.get("evidence_types", []),
                },
                "expected": "All sub-hypotheses supported",
            },
        )

    def _decompose_hypothesis(self, hypothesis: str) -> List[str]:
        """Decompose a complex hypothesis into simpler parts."""
        # Simple decomposition logic - split on common conjunctions
        conjunctions = ["∧", "AND", "&"]

        for conj in conjunctions:
            if conj in hypothesis:
                parts = hypothesis.split(conj)
                return [part.strip() for part in parts if part.strip()]

        # If no conjunctions found, try splitting on " and "
        if " and " in hypothesis:
            parts = hypothesis.split(" and ")
            return [part.strip() for part in parts if part.strip()]

        # Fallback: return original hypothesis
        return [hypothesis]

    def estimate_success_probability(self, context: StrategyContext) -> float:
        """Estimate success probability."""
        if self._has_complex_hypothesis(context.current_step):
            return 0.8  # High probability for complex hypotheses
        return 0.3  # Low probability for simple hypotheses
