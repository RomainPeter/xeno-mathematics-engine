"""
Strategy API for 2-category transformations.
Defines interfaces for strategies, rewrite plans, guards, and checkers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RewriteOperation(Enum):
    """Types of rewrite operations."""

    INSERT = "insert"
    REPLACE = "replace"
    BRANCH = "branch"
    PARAMS_PATCH = "params_patch"


@dataclass
class RewritePlan:
    """A plan for rewriting a step or plan."""

    operation: RewriteOperation
    at: str  # Step ID or position
    steps: Optional[List[Dict[str, Any]]] = None
    with_step: Optional[Dict[str, Any]] = None
    branches: Optional[List[Dict[str, Any]]] = None
    params_patch: Optional[Dict[str, Any]] = None


@dataclass
class Guards:
    """Guard conditions for strategy application."""

    max_depth: int = 2
    max_rewrites_per_fr: int = 1
    stop_if_plan_grows: bool = True
    max_plan_size_increase: int = 2


@dataclass
class StrategyContext:
    """Context for strategy application."""

    failreason: str
    operator: str
    plan: Dict[str, Any]
    current_step: Dict[str, Any]
    history: List[Dict[str, Any]]
    budgets: Dict[str, Any]
    depth: int = 0  # Explicit depth counter for rewrite operations


class Strategy(ABC):
    """Abstract base class for 2-category strategies."""

    def __init__(self, id: str, trigger_codes: List[str], expected_outcomes: List[str]):
        self.id = id
        self.trigger_codes = trigger_codes
        self.expected_outcomes = expected_outcomes
        self.guards = Guards()

    @abstractmethod
    def can_apply(self, context: StrategyContext) -> bool:
        """Check if strategy can be applied to the given context."""
        pass

    @abstractmethod
    def create_rewrite_plan(self, context: StrategyContext) -> RewritePlan:
        """Create a rewrite plan for the given context."""
        pass

    @abstractmethod
    def estimate_success_probability(self, context: StrategyContext) -> float:
        """Estimate probability of success (0.0-1.0)."""
        pass


class Checker(ABC):
    """Abstract base class for checking strategy application validity."""

    @abstractmethod
    def check_cycle_detection(
        self, plan: Dict[str, Any], history: List[Dict[str, Any]]
    ) -> bool:
        """Check for cycles in the plan."""
        pass

    @abstractmethod
    def check_depth_limit(self, depth: int, max_depth: int) -> bool:
        """Check if depth is within limits."""
        pass

    @abstractmethod
    def check_budget_constraints(
        self,
        original_plan: Dict[str, Any],
        new_plan: Dict[str, Any],
        budgets: Dict[str, Any],
    ) -> bool:
        """Check if budget constraints are respected."""
        pass

    @abstractmethod
    def check_expected_outcomes(
        self, strategy: Strategy, context: StrategyContext
    ) -> bool:
        """Check if expected outcomes are plausible."""
        pass


class StrategyRegistry:
    """Registry for managing available strategies."""

    def __init__(self):
        self._strategies: Dict[str, Strategy] = {}
        self._by_failreason: Dict[str, List[str]] = {}

    def register(self, strategy: Strategy) -> None:
        """Register a strategy."""
        self._strategies[strategy.id] = strategy
        for code in strategy.trigger_codes:
            if code not in self._by_failreason:
                self._by_failreason[code] = []
            self._by_failreason[code].append(strategy.id)

    def get_by_failreason(self, failreason: str) -> List[Strategy]:
        """Get strategies that can handle a specific failreason."""
        strategy_ids = self._by_failreason.get(failreason, [])
        return [self._strategies[sid] for sid in strategy_ids]

    def get_all(self) -> List[Strategy]:
        """Get all registered strategies."""
        return list(self._strategies.values())

    def get(self, strategy_id: str) -> Optional[Strategy]:
        """Get a specific strategy by ID."""
        return self._strategies.get(strategy_id)


class StrategySelector(ABC):
    """Abstract base class for selecting strategies."""

    @abstractmethod
    def select_strategy(
        self, context: StrategyContext, candidates: List[Strategy]
    ) -> Tuple[Optional[Strategy], float, str]:
        """
        Select the best strategy for the given context.
        Returns (strategy, confidence_score, rationale).
        """
        pass


class DeterministicSelector(StrategySelector):
    """Deterministic strategy selector (fallback)."""

    def select_strategy(
        self, context: StrategyContext, candidates: List[Strategy]
    ) -> Tuple[Optional[Strategy], float, str]:
        """Select first applicable strategy deterministically."""
        for strategy in candidates:
            if strategy.can_apply(context):
                return strategy, 1.0, f"Deterministic selection of {strategy.id}"
        return None, 0.0, "No applicable strategy found"
