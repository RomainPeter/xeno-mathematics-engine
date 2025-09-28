"""
Next-Closure implementation for Formal Concept Analysis (FCA).
Implements the Next-Closure algorithm for Attribute Exploration.
"""

from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

from .ae_engine import AEEngine, AEContext, AEResult


@dataclass
class FormalContext:
    """Formal context for FCA."""

    objects: List[str]
    attributes: List[str]
    incidence: Dict[Tuple[str, str], bool]  # (object, attribute) -> bool


@dataclass
class FormalConcept:
    """Formal concept (extent, intent)."""

    extent: Set[str]  # Objects
    intent: Set[str]  # Attributes
    support: float  # Support count
    confidence: float  # Confidence measure


class NextClosureEngine(AEEngine):
    """Next-Closure algorithm implementation for Attribute Exploration."""

    def __init__(self):
        self.context: Optional[FormalContext] = None
        self.concepts: List[FormalConcept] = []
        self.implications: List[Dict[str, Any]] = []
        self.initialized = False

    async def initialize(self, domain_spec: Dict[str, Any]) -> None:
        """Initialize the engine with domain specification."""
        self.context = self._build_formal_context(domain_spec)
        self.concepts = []
        self.implications = []
        self.initialized = True

    async def next_closure_step(self, ctx: AEContext) -> AEResult:
        """Execute one step of Next-Closure algorithm."""
        if not self.initialized or not self.context:
            raise RuntimeError("Engine not initialized")

        start_time = datetime.now()

        try:
            # Generate next concept using Next-Closure
            concept = await self._next_closure_step()

            # Generate implications from concept
            implications = await self._generate_implications(concept)

            # Update state
            self.concepts.append(concept)
            self.implications.extend(implications)

            # Calculate metrics
            timings = {
                "total": (datetime.now() - start_time).total_seconds(),
                "concept_generation": 0.1,  # Mock timing
                "implication_generation": 0.05,
            }

            metrics = {
                "concepts_count": len(self.concepts),
                "implications_count": len(self.implications),
                "concept_support": concept.support,
                "concept_confidence": concept.confidence,
            }

            return AEResult(
                step_id=ctx.step_id,
                success=True,
                concepts=[self._concept_to_dict(concept)],
                implications=implications,
                counterexamples=[],
                metrics=metrics,
                timings=timings,
            )

        except Exception as e:
            return AEResult(
                step_id=ctx.step_id,
                success=False,
                concepts=[],
                implications=[],
                counterexamples=[],
                metrics={},
                timings={"total": (datetime.now() - start_time).total_seconds()},
                error=str(e),
            )

    async def cleanup(self) -> None:
        """Cleanup resources."""
        self.context = None
        self.concepts = []
        self.implications = []
        self.initialized = False

    def _build_formal_context(self, domain_spec: Dict[str, Any]) -> FormalContext:
        """Build formal context from domain specification."""
        # Extract objects and attributes from domain spec
        objects = domain_spec.get("objects", ["obj1", "obj2", "obj3", "obj4"])
        attributes = domain_spec.get("attributes", ["attr1", "attr2", "attr3"])

        # Build incidence relation (mock for now)
        incidence = {}
        for obj in objects:
            for attr in attributes:
                # Mock incidence: some objects have some attributes
                incidence[(obj, attr)] = hash(f"{obj}_{attr}") % 3 == 0

        return FormalContext(
            objects=objects, attributes=attributes, incidence=incidence
        )

    async def _next_closure_step(self) -> FormalConcept:
        """Execute one step of Next-Closure algorithm."""
        if not self.context:
            raise RuntimeError("Context not initialized")

        # Find next concept in lectic order
        if not self.concepts:
            # First concept: empty extent, full intent
            extent = set()
            intent = set(self.context.attributes)
        else:
            # Find next concept using Next-Closure
            extent, intent = await self._next_closure(self.concepts[-1])

        # Calculate support and confidence
        support = (
            len(extent) / len(self.context.objects) if self.context.objects else 0.0
        )
        confidence = (
            len(intent) / len(self.context.attributes)
            if self.context.attributes
            else 0.0
        )

        return FormalConcept(
            extent=extent, intent=intent, support=support, confidence=confidence
        )

    async def _next_closure(
        self, previous_concept: FormalConcept
    ) -> Tuple[Set[str], Set[str]]:
        """Compute next concept in lectic order."""
        if not self.context:
            raise RuntimeError("Context not initialized")

        # Start with previous concept's extent
        extent = previous_concept.extent.copy()
        intent = previous_concept.intent.copy()

        # Find next attribute in lectic order
        for attr in reversed(self.context.attributes):
            if attr in intent:
                # Remove attribute and compute closure
                intent.remove(attr)
                extent = await self._compute_extent(intent)
                intent = await self._compute_intent(extent)
                break

        return extent, intent

    async def _compute_extent(self, intent: Set[str]) -> Set[str]:
        """Compute extent (objects) for given intent (attributes)."""
        if not self.context:
            return set()

        extent = set()
        for obj in self.context.objects:
            # Object is in extent if it has all attributes in intent
            if all(self.context.incidence.get((obj, attr), False) for attr in intent):
                extent.add(obj)

        return extent

    async def _compute_intent(self, extent: Set[str]) -> Set[str]:
        """Compute intent (attributes) for given extent (objects)."""
        if not self.context:
            return set()

        if not extent:
            return set(self.context.attributes)

        intent = set()
        for attr in self.context.attributes:
            # Attribute is in intent if all objects in extent have it
            if all(self.context.incidence.get((obj, attr), False) for obj in extent):
                intent.add(attr)

        return intent

    async def _generate_implications(
        self, concept: FormalConcept
    ) -> List[Dict[str, Any]]:
        """Generate implications from concept."""
        implications = []

        # Generate implications from concept intent
        if len(concept.intent) > 1:
            for attr in concept.intent:
                premise = list(concept.intent - {attr})
                conclusion = [attr]

                implication = {
                    "id": f"impl_{len(self.implications) + len(implications)}",
                    "premises": premise,
                    "conclusions": conclusion,
                    "support": concept.support,
                    "confidence": concept.confidence,
                    "concept_id": f"concept_{len(self.concepts)}",
                    "timestamp": datetime.now().isoformat(),
                }
                implications.append(implication)

        return implications

    def _concept_to_dict(self, concept: FormalConcept) -> Dict[str, Any]:
        """Convert FormalConcept to dictionary."""
        return {
            "id": f"concept_{len(self.concepts)}",
            "extent": list(concept.extent),
            "intent": list(concept.intent),
            "support": concept.support,
            "confidence": concept.confidence,
            "timestamp": datetime.now().isoformat(),
        }
