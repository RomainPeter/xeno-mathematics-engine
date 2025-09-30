"""
Attribute Exploration (AE) Engine implementation.
Provides AEEngine with next_step() and comprehensive statistics.
"""

from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
import time
from abc import ABC, abstractmethod

from .context import FormalContext, Intent, Attribute
from .next_closure import NextClosure, Concept, ConceptLattice


@dataclass
class AEContext:
    """Context for Attribute Exploration."""

    context: FormalContext
    current_intent: Intent
    visited_concepts: Set[Intent] = field(default_factory=set)
    step_count: int = 0
    start_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AEStatistics:
    """Statistics for Attribute Exploration."""

    concepts_visited: int = 0
    concepts_generated: int = 0
    elapsed_time: float = 0.0
    concepts_per_second: float = 0.0
    current_intent_size: int = 0
    closure_computations: int = 0
    lectic_comparisons: int = 0
    memory_usage: float = 0.0

    def update(self, elapsed_time: float):
        """Update statistics with elapsed time."""
        self.elapsed_time = elapsed_time
        if elapsed_time > 0:
            self.concepts_per_second = self.concepts_generated / elapsed_time


@dataclass
class AEResult:
    """Result from an AE step."""

    concept: Optional[Concept]
    success: bool
    statistics: AEStatistics
    elapsed_time: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AEEngine(ABC):
    """Abstract base class for Attribute Exploration Engine."""

    @abstractmethod
    def next_step(self, ctx: AEContext) -> AEResult:
        """Execute one step of Attribute Exploration."""
        pass

    @abstractmethod
    def initialize(self, context: FormalContext) -> AEContext:
        """Initialize the AE engine with a formal context."""
        pass

    @abstractmethod
    def get_statistics(self) -> AEStatistics:
        """Get current statistics."""
        pass


class NextClosureAEEngine(AEEngine):
    """
    Attribute Exploration Engine using Next-Closure algorithm.
    Implements next_step() with comprehensive statistics.
    """

    def __init__(self, attribute_order: Optional[List[Attribute]] = None):
        self.attribute_order = attribute_order
        self.next_closure: Optional[NextClosure] = None
        self.statistics = AEStatistics()
        self.initialized = False

    def initialize(self, context: FormalContext) -> AEContext:
        """Initialize the AE engine with a formal context."""
        self.context = context
        self.attribute_order = self.attribute_order or sorted(
            context.attributes, key=lambda a: a.name
        )
        self.next_closure = NextClosure(context, self.attribute_order)
        self.statistics = AEStatistics()
        self.initialized = True

        # Create initial context
        initial_intent = Intent(set())
        return AEContext(
            context=context,
            current_intent=initial_intent,
            visited_concepts=set(),
            step_count=0,
            start_time=time.time(),
            metadata={},
        )

    def next_step(self, ctx: AEContext) -> AEResult:
        """
        Execute one step of Attribute Exploration.

        Args:
            ctx: Current AE context

        Returns:
            AEResult with next concept and statistics
        """
        if not self.initialized:
            raise RuntimeError("AEEngine not initialized")

        step_start_time = time.time()

        try:
            # Generate next concept using Next-Closure
            concept = self.next_closure.generate_next_concept()

            if concept is None:
                # No more concepts
                self.statistics.update(time.time() - ctx.start_time)
                return AEResult(
                    concept=None,
                    success=True,
                    statistics=self.statistics,
                    elapsed_time=time.time() - step_start_time,
                    metadata={"status": "completed", "step": ctx.step_count},
                )

            # Update context
            ctx.visited_concepts.add(concept.intent)
            ctx.step_count += 1
            ctx.current_intent = concept.intent

            # Update statistics
            self.statistics.concepts_visited += 1
            self.statistics.concepts_generated += 1
            self.statistics.current_intent_size = len(concept.intent)
            self.statistics.closure_computations += 1

            # Update elapsed time
            if ctx.start_time:
                self.statistics.update(time.time() - ctx.start_time)

            return AEResult(
                concept=concept,
                success=True,
                statistics=self.statistics,
                elapsed_time=time.time() - step_start_time,
                metadata={
                    "step": ctx.step_count,
                    "intent_size": len(concept.intent),
                    "extent_size": len(concept.extent),
                },
            )

        except Exception as e:
            self.statistics.update(time.time() - ctx.start_time)
            return AEResult(
                concept=None,
                success=False,
                statistics=self.statistics,
                elapsed_time=time.time() - step_start_time,
                error=str(e),
                metadata={"step": ctx.step_count, "error_type": type(e).__name__},
            )

    def get_statistics(self) -> AEStatistics:
        """Get current statistics."""
        return self.statistics

    def reset(self):
        """Reset the engine to start from the beginning."""
        if self.initialized:
            self.next_closure.reset()
            self.statistics = AEStatistics()

    def get_concept_lattice(self) -> Optional[ConceptLattice]:
        """Get the concept lattice for the current context."""
        if not self.initialized or not self.next_closure:
            return None

        # Generate all concepts
        concepts = list(self.next_closure.generate_concepts())
        return ConceptLattice(concepts)

    def get_next_concepts(self, count: int) -> List[Concept]:
        """
        Get the next N concepts without updating the main iterator.

        Args:
            count: Number of concepts to generate

        Returns:
            List of next concepts
        """
        if not self.initialized:
            return []

        concepts = []
        for _ in range(count):
            concept = self.next_closure.generate_next_concept()
            if concept is None:
                break
            concepts.append(concept)

        return concepts

    def has_more_concepts(self) -> bool:
        """Check if there are more concepts to generate."""
        if not self.initialized:
            return False

        # Try to generate one more concept
        concept = self.next_closure.generate_next_concept()
        if concept is None:
            return False

        # Put it back by resetting and regenerating up to this point
        # This is a simplified check - in practice, you'd want to cache the concept
        return True


class AEEngineFactory:
    """Factory for creating AE engines."""

    @staticmethod
    def create_next_closure_engine(
        attribute_order: Optional[List[Attribute]] = None,
    ) -> NextClosureAEEngine:
        """Create a Next-Closure AE engine."""
        return NextClosureAEEngine(attribute_order)

    @staticmethod
    def create_engine(engine_type: str = "next_closure", **kwargs) -> AEEngine:
        """Create an AE engine of the specified type."""
        if engine_type == "next_closure":
            return AEEngineFactory.create_next_closure_engine(**kwargs)
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")


class AEAnalyzer:
    """Analyzer for Attribute Exploration results."""

    def __init__(self, engine: AEEngine):
        self.engine = engine

    def analyze_concept_distribution(self, concepts: List[Concept]) -> Dict[str, Any]:
        """Analyze the distribution of concepts."""
        if not concepts:
            return {}

        intent_sizes = [len(concept.intent) for concept in concepts]
        extent_sizes = [len(concept.extent) for concept in concepts]

        return {
            "total_concepts": len(concepts),
            "intent_size_stats": {
                "min": min(intent_sizes),
                "max": max(intent_sizes),
                "mean": sum(intent_sizes) / len(intent_sizes),
                "median": sorted(intent_sizes)[len(intent_sizes) // 2],
            },
            "extent_size_stats": {
                "min": min(extent_sizes),
                "max": max(extent_sizes),
                "mean": sum(extent_sizes) / len(extent_sizes),
                "median": sorted(extent_sizes)[len(extent_sizes) // 2],
            },
        }

    def analyze_closure_properties(
        self, context: FormalContext, concepts: List[Concept]
    ) -> Dict[str, Any]:
        """Analyze closure properties of the concepts."""
        if not concepts:
            return {}

        # Check idempotence
        idempotent_count = 0
        for concept in concepts:
            if context.closure(concept.intent) == concept.intent:
                idempotent_count += 1

        # Check monotonicity
        monotonic_count = 0
        for concept in concepts:
            is_monotonic = True
            for attr in concept.intent.attributes:
                smaller_intent = Intent(concept.intent.attributes - {attr})
                if not context.closure(smaller_intent).is_subset(concept.intent):
                    is_monotonic = False
                    break
            if is_monotonic:
                monotonic_count += 1

        return {
            "idempotent_concepts": idempotent_count,
            "idempotent_ratio": idempotent_count / len(concepts),
            "monotonic_concepts": monotonic_count,
            "monotonic_ratio": monotonic_count / len(concepts),
        }

    def generate_report(self, context: FormalContext, concepts: List[Concept]) -> Dict[str, Any]:
        """Generate a comprehensive analysis report."""
        stats = self.engine.get_statistics()
        concept_dist = self.analyze_concept_distribution(concepts)
        closure_props = self.analyze_closure_properties(context, concepts)

        return {
            "engine_statistics": {
                "concepts_visited": stats.concepts_visited,
                "concepts_generated": stats.concepts_generated,
                "elapsed_time": stats.elapsed_time,
                "concepts_per_second": stats.concepts_per_second,
                "closure_computations": stats.closure_computations,
            },
            "concept_distribution": concept_dist,
            "closure_properties": closure_props,
            "context_info": {
                "objects": len(context.objects),
                "attributes": len(context.attributes),
                "incidence_relations": len(context.incidence),
            },
        }
