"""
AE Engine interface for Attribute Exploration using Next-Closure algorithm.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class AEContext:
    """Context for AE operations."""

    run_id: str
    step_id: str
    trace_id: str
    domain_spec: Dict[str, Any]
    state: Dict[str, Any]
    budgets: Dict[str, Any]
    thresholds: Dict[str, Any]


@dataclass
class AEResult:
    """Result from AE step."""

    step_id: str
    success: bool
    concepts: List[Dict[str, Any]]
    implications: List[Dict[str, Any]]
    counterexamples: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    timings: Dict[str, float]
    error: Optional[str] = None


class AEEngine(ABC):
    """Abstract base class for Attribute Exploration engines."""

    @abstractmethod
    async def next_closure_step(self, ctx: AEContext) -> AEResult:
        """
        Execute one step of Next-Closure algorithm.

        Args:
            ctx: AE context with state and configuration

        Returns:
            AEResult with concepts, implications, and metrics
        """
        pass

    @abstractmethod
    async def initialize(self, domain_spec: Dict[str, Any]) -> None:
        """
        Initialize the AE engine with domain specification.

        Args:
            domain_spec: Domain-specific configuration
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass
