"""
Execution modes for 2-category transformations.
Implements shadow mode and active gated mode.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from .strategy_api import StrategyContext, StrategySelector, StrategyRegistry
from .rewriter import PlanRewriter


class ExecutionMode(Enum):
    """Execution modes for 2-category transformations."""

    SHADOW = "shadow"
    ACTIVE_GATED = "active_gated"


@dataclass
class ShadowReport:
    """Report from shadow mode execution."""

    mode: str
    timestamp: str
    proposals: List[Dict[str, Any]]
    total_strategies_evaluated: int
    applicable_strategies: int
    success_rate: float


@dataclass
class ActiveResult:
    """Result from active mode execution."""

    success: bool
    applied_strategy: Optional[str]
    new_plan: Optional[Dict[str, Any]]
    two_cell: Optional[Dict[str, Any]]
    confidence: float
    rationale: str
    error: Optional[str] = None


class TwoCategoryOrchestrator:
    """Orchestrator for 2-category transformations."""

    def __init__(
        self,
        strategy_registry: StrategyRegistry,
        rewriter: PlanRewriter,
        selector: StrategySelector,
    ):
        self.strategy_registry = strategy_registry
        self.rewriter = rewriter
        self.selector = selector

    def execute_shadow_mode(self, context: StrategyContext) -> ShadowReport:
        """Execute in shadow mode - generate proposals without applying."""
        proposals = []
        applicable_strategies = 0
        total_strategies = 0

        # Get candidate strategies for the failreason
        candidates = self.strategy_registry.get_by_failreason(context.failreason)
        total_strategies = len(candidates)

        for strategy in candidates:
            if strategy.can_apply(context):
                applicable_strategies += 1

                # Create rewrite plan (but don't apply)
                try:
                    rewrite_plan = strategy.create_rewrite_plan(context)
                    success_prob = strategy.estimate_success_probability(context)

                    proposal = {
                        "strategy_id": strategy.id,
                        "failreason": context.failreason,
                        "operator": context.operator,
                        "rewrite_plan": {
                            "operation": rewrite_plan.operation.value,
                            "at": rewrite_plan.at,
                            "steps": rewrite_plan.steps,
                            "with_step": rewrite_plan.with_step,
                            "branches": rewrite_plan.branches,
                            "params_patch": rewrite_plan.params_patch,
                        },
                        "success_probability": success_prob,
                        "expected_outcomes": strategy.expected_outcomes,
                        "guards": {
                            "max_depth": strategy.guards.max_depth,
                            "max_rewrites_per_fr": strategy.guards.max_rewrites_per_fr,
                        },
                    }
                    proposals.append(proposal)
                except Exception as e:
                    # Log error but continue
                    print(f"Error creating proposal for {strategy.id}: {e}")

        success_rate = (
            applicable_strategies / total_strategies if total_strategies > 0 else 0.0
        )

        return ShadowReport(
            mode="shadow",
            timestamp=datetime.now().isoformat(),
            proposals=proposals,
            total_strategies_evaluated=total_strategies,
            applicable_strategies=applicable_strategies,
            success_rate=success_rate,
        )

    def execute_active_gated_mode(
        self, context: StrategyContext, confidence_threshold: float = 0.7
    ) -> ActiveResult:
        """Execute in active gated mode - apply strategy if conditions are met."""

        # Get candidate strategies
        candidates = self.strategy_registry.get_by_failreason(context.failreason)

        if not candidates:
            return ActiveResult(
                success=False,
                error=f"No strategies available for failreason: {context.failreason}",
            )

        # Select best strategy
        strategy, confidence, rationale = self.selector.select_strategy(
            context, candidates
        )

        if not strategy:
            return ActiveResult(success=False, error="No applicable strategy found")

        if confidence < confidence_threshold:
            return ActiveResult(
                success=False,
                error=f"Confidence too low: {confidence:.2f} < {confidence_threshold:.2f}",
            )

        # Apply the strategy
        result = self.rewriter.apply_strategy(strategy, context.plan, context)

        if not result.success:
            return ActiveResult(success=False, error=result.error)

        return ActiveResult(
            success=True,
            applied_strategy=strategy.id,
            new_plan=result.new_plan,
            two_cell=result.two_cell,
            confidence=confidence,
            rationale=rationale,
        )

    def save_shadow_report(self, report: ShadowReport, output_path: str) -> None:
        """Save shadow report to file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "mode": report.mode,
                    "timestamp": report.timestamp,
                    "proposals": report.proposals,
                    "total_strategies_evaluated": report.total_strategies_evaluated,
                    "applicable_strategies": report.applicable_strategies,
                    "success_rate": report.success_rate,
                },
                f,
                indent=2,
            )

    def save_two_cells(self, two_cells: List[Dict[str, Any]], output_path: str) -> None:
        """Save two_cells to JSONL file."""
        with open(output_path, "w", encoding="utf-8") as f:
            for two_cell in two_cells:
                f.write(json.dumps(two_cell) + "\n")

    def load_strategies_from_yaml(self, yaml_path: str) -> None:
        """Load strategies from YAML configuration."""
        # This would be implemented to load strategy definitions from YAML
        # For now, we'll implement this in the strategy implementations
        pass
