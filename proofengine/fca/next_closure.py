"""
Next-Closure algorithm for Formal Concept Analysis.
Implements the Next-Closure algorithm with lectic order and concept iteration.
"""

from typing import List, Iterator, Optional, Set
from dataclasses import dataclass
import time

from .context import FormalContext, Intent, Attribute, Extent


def lectic_leq(
    intent1: Intent, intent2: Intent, attribute_order: List[Attribute]
) -> bool:
    """
    Check if intent1 is lectically less than or equal to intent2.

    Args:
        intent1: First intent
        intent2: Second intent
        attribute_order: Total order on attributes for lectic comparison

    Returns:
        True if intent1 <=_lect intent2
    """
    # Find the first attribute where the intents differ
    for attr in reversed(attribute_order):
        has_attr1 = attr in intent1.attributes
        has_attr2 = attr in intent2.attributes

        if has_attr1 != has_attr2:
            return (
                not has_attr1
            )  # intent1 <= intent2 if intent1 doesn't have attr but intent2 does

    return True  # intents are equal


def closure(context: FormalContext, intent: Intent) -> Intent:
    """
    Compute closure of an intent in a formal context.

    Args:
        context: Formal context
        intent: Intent to compute closure for

    Returns:
        Closure of the intent
    """
    return context.closure(intent)


@dataclass
class Concept:
    """Formal concept (extent, intent) pair."""

    extent: Extent
    intent: Intent

    def __str__(self) -> str:
        return f"({self.extent}, {self.intent})"

    def __repr__(self) -> str:
        return f"Concept(extent={self.extent}, intent={self.intent})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Concept):
            return False
        return self.extent == other.extent and self.intent == other.intent

    def __hash__(self) -> int:
        return hash((self.extent, self.intent))


class NextClosure:
    """
    Next-Closure algorithm implementation.
    Generates concepts in lectic order using the Next-Closure algorithm.
    """

    def __init__(
        self, context: FormalContext, attribute_order: Optional[List[Attribute]] = None
    ):
        self.context = context
        self.attribute_order = attribute_order or sorted(
            context.attributes, key=lambda a: a.name
        )
        self._visited_concepts: Set[Intent] = set()
        self._concept_count = 0
        self._start_time: Optional[float] = None

    def __iter__(self) -> Iterator[Concept]:
        """Iterate over all concepts in lectic order."""
        return self.generate_concepts()

    def generate_concepts(self) -> Iterator[Concept]:
        """
        Generate all concepts using Next-Closure algorithm.

        Yields:
            Concepts in lectic order
        """
        self._start_time = time.time()
        self._visited_concepts.clear()
        self._concept_count = 0

        # Start with empty intent
        current_intent = Intent(set())

        while True:
            # Compute closure of current intent
            closed_intent = self.context.closure(current_intent)

            # Check if we've already visited this concept
            if closed_intent in self._visited_concepts:
                break

            # Create concept
            extent = self.context.extent(closed_intent)
            concept = Concept(extent=extent, intent=closed_intent)

            # Mark as visited
            self._visited_concepts.add(closed_intent)
            self._concept_count += 1

            yield concept

            # Find next intent in lectic order
            next_intent = self._next_closure(closed_intent)
            if next_intent is None:
                break

            current_intent = next_intent

    def _next_closure(self, current_intent: Intent) -> Optional[Intent]:
        """
        Find the next closed intent in lectic order.

        Args:
            current_intent: Current intent

        Returns:
            Next closed intent or None if no more concepts
        """
        # Try to add attributes in reverse lectic order
        for attr in reversed(self.attribute_order):
            if attr not in current_intent.attributes:
                # Create new intent by adding this attribute
                new_intent = Intent(current_intent.attributes | {attr})

                # Compute closure
                closed_intent = self.context.closure(new_intent)

                # Check if this is the next concept in lectic order
                if lectic_leq(current_intent, closed_intent, self.attribute_order):
                    return closed_intent

        return None

    def get_statistics(self) -> dict:
        """Get algorithm statistics."""
        elapsed_time = 0.0
        if self._start_time is not None:
            elapsed_time = time.time() - self._start_time

        return {
            "concepts_generated": self._concept_count,
            "elapsed_time": elapsed_time,
            "concepts_per_second": self._concept_count / max(elapsed_time, 0.001),
            "visited_concepts": len(self._visited_concepts),
        }

    def generate_next_concept(self) -> Optional[Concept]:
        """
        Generate the next concept in the sequence.

        Returns:
            Next concept or None if no more concepts
        """
        if not hasattr(self, "_concept_iterator"):
            self._concept_iterator = iter(self.generate_concepts())

        try:
            return next(self._concept_iterator)
        except StopIteration:
            return None

    def reset(self):
        """Reset the algorithm to start from the beginning."""
        self._visited_concepts.clear()
        self._concept_count = 0
        self._start_time = None
        if hasattr(self, "_concept_iterator"):
            delattr(self, "_concept_iterator")


class ConceptLattice:
    """
    Concept lattice with ordering relations.
    Provides methods to navigate the concept lattice.
    """

    def __init__(self, concepts: List[Concept]):
        self.concepts = concepts
        self._concept_to_index = {concept: i for i, concept in enumerate(concepts)}
        self._subconcept_relations: List[Set[int]] = [set() for _ in concepts]
        self._superconcept_relations: List[Set[int]] = [set() for _ in concepts]

        # Build ordering relations
        self._build_ordering_relations()

    def _build_ordering_relations(self):
        """Build subconcept-superconcept relations."""
        for i, concept1 in enumerate(self.concepts):
            for j, concept2 in enumerate(self.concepts):
                if i != j:
                    # concept1 is subconcept of concept2 if extent1 is subset of extent2
                    if concept1.extent.is_subset(concept2.extent):
                        self._subconcept_relations[i].add(j)
                        self._superconcept_relations[j].add(i)

    def get_subconcepts(self, concept: Concept) -> List[Concept]:
        """Get all subconcepts of a concept."""
        if concept not in self._concept_to_index:
            return []

        index = self._concept_to_index[concept]
        return [self.concepts[i] for i in self._subconcept_relations[index]]

    def get_superconcepts(self, concept: Concept) -> List[Concept]:
        """Get all superconcepts of a concept."""
        if concept not in self._concept_to_index:
            return []

        index = self._concept_to_index[concept]
        return [self.concepts[i] for i in self._superconcept_relations[index]]

    def get_immediate_subconcepts(self, concept: Concept) -> List[Concept]:
        """Get immediate subconcepts (direct children)."""
        subconcepts = self.get_subconcepts(concept)

        # Filter to immediate subconcepts (no intermediate concepts)
        immediate = []
        for subconcept in subconcepts:
            is_immediate = True
            for other_subconcept in subconcepts:
                if (
                    other_subconcept != subconcept
                    and other_subconcept.extent.is_subset(subconcept.extent)
                ):
                    is_immediate = False
                    break

            if is_immediate:
                immediate.append(subconcept)

        return immediate

    def get_immediate_superconcepts(self, concept: Concept) -> List[Concept]:
        """Get immediate superconcepts (direct parents)."""
        superconcepts = self.get_superconcepts(concept)

        # Filter to immediate superconcepts (no intermediate concepts)
        immediate = []
        for superconcept in superconcepts:
            is_immediate = True
            for other_superconcept in superconcepts:
                if (
                    other_superconcept != superconcept
                    and superconcept.extent.is_subset(other_superconcept.extent)
                ):
                    is_immediate = False
                    break

            if is_immediate:
                immediate.append(superconcept)

        return immediate

    def get_bottom_concept(self) -> Optional[Concept]:
        """Get the bottom concept (smallest extent)."""
        if not self.concepts:
            return None

        return min(self.concepts, key=lambda c: len(c.extent))

    def get_top_concept(self) -> Optional[Concept]:
        """Get the top concept (largest extent)."""
        if not self.concepts:
            return None

        return max(self.concepts, key=lambda c: len(c.extent))

    def __len__(self) -> int:
        return len(self.concepts)

    def __iter__(self) -> Iterator[Concept]:
        return iter(self.concepts)

    def __getitem__(self, index: int) -> Concept:
        return self.concepts[index]
