"""
LLM-based strategy selector with auto-consistency and explainable scoring.

Uses Kimi K2 via OpenRouter with n=3 auto-consistency voting,
multi-criteria scoring, and deterministic fallback.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from proofengine.core.llm_client import LLMClient, LLMRequest, get_llm_client
from proofengine.orchestrator.strategy_api import Strategy, StrategyContext


@dataclass
class SelectionResult:
    """Result of strategy selection."""

    strategy_id: str
    score: float
    confidence: float
    reason: str
    expected_gain: float
    risk_assessment: str
    alternatives: List[Dict[str, Any]]
    reasoning: Dict[str, Any]
    metadata: Dict[str, Any]


class StrategySelector:
    """LLM-based strategy selector with auto-consistency."""

    def __init__(self, llm_client: Optional[LLMClient] = None, use_mock: bool = False):
        """Initialize selector with LLM client."""
        self.llm_client = llm_client or get_llm_client(use_mock=use_mock)
        self.logger = logging.getLogger(__name__)

        # Whitelist of strategies by FailReason
        self.strategy_whitelist = {
            "contract.ambiguous_spec": ["specialize_then_retry"],
            "coverage.missing_test": ["add_missing_tests"],
            "api.semver_missing": ["require_semver"],
            "api.changelog_missing": ["changelog_or_block"],
            "runner.test_failure": ["decompose_meet"],
            "nondet.flaky_test": ["retry_with_hardening"],
            "policy.dependency_pin_required": ["pin_dependency"],
            "policy.secret": ["guard_before"],
            "policy.egress": ["guard_before"],
        }

        # Scoring weights
        self.scoring_weights = {
            "validity": 0.3,  # JSON validity vs output schema
            "cost_efficiency": 0.2,  # Predicted cost vs expected gain
            "historical_success": 0.25,  # Success rate by FailReason
            "output_size": 0.1,  # Reasonable output size
            "entropy": 0.15,  # Decision confidence/entropy
        }

    def select_strategy(
        self, context: StrategyContext, available_strategies: List[Strategy]
    ) -> SelectionResult:
        """Select best strategy using LLM with auto-consistency."""

        # Filter strategies by whitelist
        applicable_strategies = self._filter_by_whitelist(available_strategies, context.failreason)

        if not applicable_strategies:
            return self._fallback_selection(context, available_strategies)

        # Create LLM prompt
        prompt = self._create_selection_prompt(context, applicable_strategies)

        # Get LLM response with auto-consistency
        try:
            request = LLMRequest(
                prompt=prompt,
                temperature=0.0,  # Deterministic
                n=3,  # Auto-consistency
                model="kimi/kimi-2",
            )

            response = self.llm_client.generate(request)

            # Parse and validate response
            selection = self._parse_llm_response(response.content)

            # Apply multi-criteria scoring
            scored_selection = self._apply_scoring(selection, context, applicable_strategies)

            return scored_selection

        except Exception as e:
            self.logger.error(f"LLM selection failed: {e}")
            return self._fallback_selection(context, applicable_strategies)

    def _filter_by_whitelist(self, strategies: List[Strategy], failreason: str) -> List[Strategy]:
        """Filter strategies by FailReason whitelist."""
        allowed_ids = self.strategy_whitelist.get(failreason, [])
        return [s for s in strategies if s.id in allowed_ids]

    def _create_selection_prompt(self, context: StrategyContext, strategies: List[Strategy]) -> str:
        """Create prompt for LLM strategy selection."""

        strategies_info = []
        for strategy in strategies:
            strategies_info.append(
                {
                    "id": strategy.id,
                    "trigger_failreasons": getattr(strategy, "trigger_failreasons", []),
                    "expected_outcomes": getattr(strategy, "expected_outcomes", []),
                    "guards": {
                        "max_depth": getattr(strategy.guards, "max_depth", 2),
                        "max_rewrites_per_fr": getattr(strategy.guards, "max_rewrites_per_fr", 1),
                        "stop_if_plan_grows": getattr(strategy.guards, "stop_if_plan_grows", False),
                        "max_plan_size_increase": getattr(
                            strategy.guards, "max_plan_size_increase", 2
                        ),
                    },
                }
            )

        prompt = f"""
You are a strategy selector for 2-category transformations in a proof engine.

CONTEXT:
- FailReason: {context.failreason}
- Operator: {context.operator}
- Plan steps: {len(context.plan.get('steps', []))}
- Budgets: {context.budgets}
- History: {len(context.history)} previous transformations

AVAILABLE STRATEGIES:
{json.dumps(strategies_info, indent=2)}

TASK:
Select the best strategy for this context. Consider:
1. Strategy applicability to the FailReason
2. Expected outcomes alignment with plan goals
3. Budget constraints and efficiency
4. Risk assessment (low/medium/high)
5. Historical success patterns

Respond with valid JSON matching this schema:
{{
  "selected_strategy": {{
    "id": "strategy_id",
    "score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "reason": "explanation",
    "expected_gain": 0.0-1.0,
    "risk_assessment": "low|medium|high"
  }},
  "alternative_strategies": [
    {{"id": "alt_id", "score": 0.0, "reason": "why not chosen"}}
  ],
  "reasoning": {{
    "analysis": "detailed analysis",
    "constraints_considered": ["budget", "depth", "cycles"],
    "budget_impact": {{"time_delta": 0, "cost_delta": 0.0}}
  }}
}}

Be deterministic and explainable. Focus on practical applicability.
"""
        return prompt

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse and validate LLM response."""
        try:
            # Extract JSON from response
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")

            json_str = content[start_idx:end_idx]
            response = json.loads(json_str)

            # Validate required fields
            if "selected_strategy" not in response:
                raise ValueError("Missing selected_strategy in response")

            return response

        except Exception as e:
            self.logger.error(f"Failed to parse LLM response: {e}")
            raise ValueError(f"Invalid LLM response format: {e}")

    def _apply_scoring(
        self,
        selection: Dict[str, Any],
        context: StrategyContext,
        strategies: List[Strategy],
    ) -> SelectionResult:
        """Apply multi-criteria scoring to selection."""

        selected = selection["selected_strategy"]
        strategy_id = selected["id"]

        # Find the actual strategy object
        strategy = next((s for s in strategies if s.id == strategy_id), None)
        if not strategy:
            raise ValueError(f"Selected strategy {strategy_id} not found in available strategies")

        # Calculate scores
        scores = self._calculate_scores(selected, strategy, context)

        # Weighted final score
        final_score = sum(
            scores.get(criteria, 0) * weight for criteria, weight in self.scoring_weights.items()
        )

        return SelectionResult(
            strategy_id=strategy_id,
            score=min(max(final_score, 0.0), 1.0),  # Clamp to [0,1]
            confidence=selected.get("confidence", 0.8),
            reason=selected.get("reason", "LLM selection"),
            expected_gain=selected.get("expected_gain", 0.5),
            risk_assessment=selected.get("risk_assessment", "medium"),
            alternatives=selection.get("alternative_strategies", []),
            reasoning=selection.get("reasoning", {}),
            metadata={
                "model": "kimi/kimi-2",
                "timestamp": context.plan.get("timestamp", 0),
                "consistency_votes": 3,
                "cache_hit": False,
            },
        )

    def _calculate_scores(
        self, selected: Dict[str, Any], strategy: Strategy, context: StrategyContext
    ) -> Dict[str, float]:
        """Calculate individual scoring criteria."""

        scores = {}

        # Validity score (JSON structure compliance)
        scores["validity"] = 1.0 if selected.get("id") and selected.get("score") else 0.0

        # Cost efficiency (predicted cost vs expected gain)
        expected_gain = selected.get("expected_gain", 0.5)
        cost_estimate = self._estimate_strategy_cost(strategy, context)
        scores["cost_efficiency"] = expected_gain / max(cost_estimate, 0.1)

        # Historical success (mock for now)
        scores["historical_success"] = self._get_historical_success_rate(
            strategy.id, context.failreason
        )

        # Output size (reasonable response length)
        reason_length = len(selected.get("reason", ""))
        scores["output_size"] = min(reason_length / 100, 1.0)  # Normalize to [0,1]

        # Entropy (decision confidence)
        confidence = selected.get("confidence", 0.8)
        scores["entropy"] = confidence

        return scores

    def _estimate_strategy_cost(self, strategy: Strategy, context: StrategyContext) -> float:
        """Estimate cost of applying strategy."""
        # Simple heuristic based on strategy complexity
        base_cost = 1.0

        # Adjust based on guards
        if hasattr(strategy.guards, "max_depth"):
            base_cost += strategy.guards.max_depth * 0.1

        if hasattr(strategy.guards, "stop_if_plan_grows") and strategy.guards.stop_if_plan_grows:
            base_cost += 0.2

        return base_cost

    def _get_historical_success_rate(self, strategy_id: str, failreason: str) -> float:
        """Get historical success rate (mock implementation)."""
        # Mock historical data
        historical_rates = {
            "specialize_then_retry": 0.85,
            "add_missing_tests": 0.78,
            "require_semver": 0.92,
            "changelog_or_block": 0.88,
            "decompose_meet": 0.75,
            "retry_with_hardening": 0.82,
            "pin_dependency": 0.90,
            "guard_before": 0.95,
        }

        return historical_rates.get(strategy_id, 0.7)

    def _fallback_selection(
        self, context: StrategyContext, strategies: List[Strategy]
    ) -> SelectionResult:
        """Deterministic fallback when LLM fails."""

        # Simple deterministic selection
        if not strategies:
            raise ValueError("No applicable strategies found")

        # Select first applicable strategy
        strategy = strategies[0]

        return SelectionResult(
            strategy_id=strategy.id,
            score=0.6,  # Medium confidence
            confidence=0.7,
            reason="Deterministic fallback selection",
            expected_gain=0.5,
            risk_assessment="medium",
            alternatives=[],
            reasoning={
                "analysis": "LLM selection failed, using deterministic fallback",
                "constraints_considered": ["availability"],
                "budget_impact": {"time_delta": 0, "cost_delta": 0.0},
            },
            metadata={
                "model": "fallback",
                "timestamp": context.plan.get("timestamp", 0),
                "consistency_votes": 1,
                "cache_hit": False,
            },
        )
