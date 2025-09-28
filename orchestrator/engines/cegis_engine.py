"""
CEGIS Engine interface for Counter-Example Guided Inductive Synthesis.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Union


@dataclass
class Candidate:
    """Synthesis candidate."""

    id: str
    specification: Dict[str, Any]
    implementation: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class Verdict:
    """Verification verdict."""

    valid: bool
    confidence: float
    evidence: List[Dict[str, Any]]
    metrics: Dict[str, Any]


@dataclass
class Counterexample:
    """Counterexample for refinement."""

    id: str
    candidate_id: str
    failing_property: str
    evidence: Dict[str, Any]
    suggestions: List[str]


@dataclass
class CegisContext:
    """Context for CEGIS operations."""

    run_id: str
    step_id: str
    trace_id: str
    specification: Dict[str, Any]
    constraints: List[Dict[str, Any]]
    budgets: Dict[str, Any]
    state: Dict[str, Any]


@dataclass
class CegisResult:
    """Result from CEGIS step."""

    step_id: str
    success: bool
    candidate: Optional[Candidate]
    verdict: Optional[Verdict]
    counterexample: Optional[Counterexample]
    metrics: Dict[str, Any]
    timings: Dict[str, float]
    error: Optional[str] = None


class CegisEngine(ABC):
    """Abstract base class for CEGIS engines."""

    @abstractmethod
    async def propose(self, ctx: CegisContext) -> Candidate:
        """
        Propose a new synthesis candidate.

        Args:
            ctx: CEGIS context with specification and constraints

        Returns:
            Candidate with specification and implementation
        """
        pass

    @abstractmethod
    async def verify(
        self, candidate: Candidate, ctx: CegisContext
    ) -> Union[Verdict, Counterexample]:
        """
        Verify a candidate against specification.

        Args:
            candidate: Candidate to verify
            ctx: CEGIS context

        Returns:
            Verdict if valid, Counterexample if invalid
        """
        pass

    @abstractmethod
    async def refine(
        self, candidate: Candidate, counterexample: Counterexample, ctx: CegisContext
    ) -> Candidate:
        """
        Refine candidate based on counterexample.

        Args:
            candidate: Original candidate
            counterexample: Counterexample to address
            ctx: CEGIS context

        Returns:
            Refined candidate
        """
        pass

    @abstractmethod
    async def initialize(self, domain_spec: Dict[str, Any]) -> None:
        """
        Initialize the CEGIS engine with domain specification.

        Args:
            domain_spec: Domain-specific configuration
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass
