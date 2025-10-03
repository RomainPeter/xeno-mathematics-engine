"""
Tests for FCA Next-Closure algorithm.
Tests contextes 4×4 et 5×3 with lectic order, no duplicates, and closure idempotence.
"""

import time

import pytest

from proofengine.fca.ae_engine import AEContext, AEResult, NextClosureAEEngine
from proofengine.fca.context import (Attribute, Extent, FormalContext, Intent,
                                     Object)
from proofengine.fca.next_closure import (Concept, ConceptLattice, NextClosure,
                                          closure, lectic_leq)


class TestFCAContexts:
    """Test cases for FCA contexts."""

    @pytest.fixture
    def context_4x4(self):
        """Create a 4×4 toy formal context."""
        objects = [Object(f"obj{i}") for i in range(1, 5)]
        attributes = [Attribute(f"attr{i}") for i in range(1, 5)]

        # Create incidence relation
        incidence = {}
        for obj in objects:
            for attr in attributes:
                # Simple pattern: obj1 has attr1,2; obj2 has attr2,3; etc.
                obj_num = int(obj.name[3])
                attr_num = int(attr.name[4])
                incidence[(obj, attr)] = (obj_num + attr_num) % 2 == 0

        return FormalContext(objects, attributes, incidence)

    @pytest.fixture
    def context_5x3(self):
        """Create a 5×3 toy formal context."""
        objects = [Object(f"obj{i}") for i in range(1, 6)]
        attributes = [Attribute(f"attr{i}") for i in range(1, 4)]

        # Create incidence relation
        incidence = {}
        for obj in objects:
            for attr in attributes:
                obj_num = int(obj.name[3])
                attr_num = int(attr.name[4])
                incidence[(obj, attr)] = (obj_num + attr_num) % 3 == 0

        return FormalContext(objects, attributes, incidence)

    @pytest.fixture
    def context_fruits(self):
        """Create a fruits context (5×3)."""
        objects = [
            Object("apple"),
            Object("banana"),
            Object("carrot"),
            Object("broccoli"),
            Object("orange"),
        ]
        attributes = [Attribute("sweet"), Attribute("fruit"), Attribute("vegetable")]

        incidence = {
            (objects[0], attributes[0]): True,  # apple: sweet
            (objects[0], attributes[1]): True,  # apple: fruit
            (objects[0], attributes[2]): False,  # apple: not vegetable
            (objects[1], attributes[0]): True,  # banana: sweet
            (objects[1], attributes[1]): True,  # banana: fruit
            (objects[1], attributes[2]): False,  # banana: not vegetable
            (objects[2], attributes[0]): False,  # carrot: not sweet
            (objects[2], attributes[1]): False,  # carrot: not fruit
            (objects[2], attributes[2]): True,  # carrot: vegetable
            (objects[3], attributes[0]): False,  # broccoli: not sweet
            (objects[3], attributes[1]): False,  # broccoli: not fruit
            (objects[3], attributes[2]): True,  # broccoli: vegetable
            (objects[4], attributes[0]): False,  # orange: not sweet (sour)
            (objects[4], attributes[1]): True,  # orange: fruit
            (objects[4], attributes[2]): False,  # orange: not vegetable
        }

        return FormalContext(objects, attributes, incidence)


class TestLecticOrder:
    """Test lectic order properties."""

    def test_lectic_leq_basic(self):
        """Test basic lectic order comparisons."""
        attr1 = Attribute("a")
        attr2 = Attribute("b")
        attr3 = Attribute("c")
        attribute_order = [attr1, attr2, attr3]

        # Empty intent is lectically smallest
        empty = Intent(set())
        intent_a = Intent({attr1})
        intent_b = Intent({attr2})
        intent_ab = Intent({attr1, attr2})

        assert lectic_leq(empty, intent_a, attribute_order)
        assert lectic_leq(empty, intent_b, attribute_order)
        assert lectic_leq(intent_a, intent_ab, attribute_order)
        assert not lectic_leq(intent_a, empty, attribute_order)
        assert not lectic_leq(intent_ab, intent_a, attribute_order)

    def test_lectic_leq_reflexive(self):
        """Test that lectic order is reflexive."""
        attr1 = Attribute("a")
        attr2 = Attribute("b")
        attribute_order = [attr1, attr2]

        intent = Intent({attr1})
        assert lectic_leq(intent, intent, attribute_order)

    def test_lectic_leq_transitive(self):
        """Test that lectic order is transitive."""
        attr1 = Attribute("a")
        attr2 = Attribute("b")
        attr3 = Attribute("c")
        attribute_order = [attr1, attr2, attr3]

        intent1 = Intent({attr1})
        intent2 = Intent({attr1, attr2})
        intent3 = Intent({attr1, attr2, attr3})

        assert lectic_leq(intent1, intent2, attribute_order)
        assert lectic_leq(intent2, intent3, attribute_order)
        assert lectic_leq(intent1, intent3, attribute_order)


class TestClosure:
    """Test closure operations."""

    def test_closure_idempotence(self, context_4x4):
        """Test that closure is idempotent."""
        # Test with various intents
        test_intents = [
            Intent(set()),  # Empty intent
            Intent({context_4x4.attributes[0]}),  # Single attribute
            Intent({context_4x4.attributes[0], context_4x4.attributes[1]}),  # Two attributes
        ]

        for intent in test_intents:
            closed_once = closure(context_4x4, intent)
            closed_twice = closure(context_4x4, closed_once)
            assert closed_once == closed_twice, f"Closure not idempotent for {intent}"

    def test_closure_monotonicity(self, context_4x4):
        """Test that closure is monotonic."""
        attr1 = context_4x4.attributes[0]
        attr2 = context_4x4.attributes[1]

        intent1 = Intent({attr1})
        intent2 = Intent({attr1, attr2})

        closed1 = closure(context_4x4, intent1)
        closed2 = closure(context_4x4, intent2)

        # If intent1 is subset of intent2, then closure(intent1) should be subset of closure(intent2)
        if intent1.is_subset(intent2):
            assert closed1.is_subset(closed2), "Closure not monotonic"

    def test_closure_extensive(self, context_4x4):
        """Test that closure is extensive (intent ⊆ closure(intent))."""
        test_intents = [
            Intent(set()),
            Intent({context_4x4.attributes[0]}),
            Intent({context_4x4.attributes[0], context_4x4.attributes[1]}),
        ]

        for intent in test_intents:
            closed = closure(context_4x4, intent)
            assert intent.is_subset(closed), f"Closure not extensive for {intent}"


class TestNextClosure:
    """Test Next-Closure algorithm."""

    def test_next_closure_4x4(self, context_4x4):
        """Test Next-Closure on 4×4 context."""
        next_closure = NextClosure(context_4x4)
        concepts = list(next_closure.generate_concepts())

        # Check that we get concepts
        assert len(concepts) > 0, "No concepts generated"

        # Check that all concepts are valid
        for concept in concepts:
            assert isinstance(concept, Concept)
            assert isinstance(concept.extent, Extent)
            assert isinstance(concept.intent, Intent)

    def test_next_closure_5x3(self, context_5x3):
        """Test Next-Closure on 5×3 context."""
        next_closure = NextClosure(context_5x3)
        concepts = list(next_closure.generate_concepts())

        # Check that we get concepts
        assert len(concepts) > 0, "No concepts generated"

        # Check that all concepts are valid
        for concept in concepts:
            assert isinstance(concept, Concept)
            assert isinstance(concept.extent, Extent)
            assert isinstance(concept.intent, Intent)

    def test_next_closure_fruits(self, context_fruits):
        """Test Next-Closure on fruits context."""
        next_closure = NextClosure(context_fruits)
        concepts = list(next_closure.generate_concepts())

        # Check that we get concepts
        assert len(concepts) > 0, "No concepts generated"

        # Check that all concepts are valid
        for concept in concepts:
            assert isinstance(concept, Concept)
            assert isinstance(concept.extent, Extent)
            assert isinstance(concept.intent, Intent)

    def test_lectic_order_respected(self, context_4x4):
        """Test that concepts are generated in lectic order."""
        next_closure = NextClosure(context_4x4)
        concepts = list(next_closure.generate_concepts())

        # Check that concepts are in lectic order
        for i in range(len(concepts) - 1):
            current_intent = concepts[i].intent
            next_intent = concepts[i + 1].intent

            assert lectic_leq(
                current_intent, next_intent, context_4x4.attributes
            ), f"Concepts not in lectic order: {current_intent} vs {next_intent}"

    def test_no_duplicates(self, context_4x4):
        """Test that no duplicate concepts are generated."""
        next_closure = NextClosure(context_4x4)
        concepts = list(next_closure.generate_concepts())

        # Check for duplicates
        intents = [concept.intent for concept in concepts]
        assert len(intents) == len(set(intents)), "Duplicate concepts found"

    def test_performance_5x3(self, context_5x3):
        """Test performance on 5×3 context (< 100ms)."""
        start_time = time.time()

        next_closure = NextClosure(context_5x3)
        concepts = list(next_closure.generate_concepts())

        elapsed_time = time.time() - start_time

        # Should complete in less than 100ms
        assert elapsed_time < 0.1, f"Performance test failed: {elapsed_time:.3f}s > 100ms"

        # Should generate some concepts
        assert len(concepts) > 0, "No concepts generated"

    def test_statistics(self, context_4x4):
        """Test that statistics are collected correctly."""
        next_closure = NextClosure(context_4x4)
        concepts = list(next_closure.generate_concepts())
        stats = next_closure.get_statistics()

        assert stats["concepts_generated"] == len(concepts)
        assert stats["elapsed_time"] > 0
        assert stats["concepts_per_second"] > 0


class TestAEEngine:
    """Test Attribute Exploration Engine."""

    def test_ae_engine_initialization(self, context_4x4):
        """Test AE engine initialization."""
        engine = NextClosureAEEngine()
        ctx = engine.initialize(context_4x4)

        assert isinstance(ctx, AEContext)
        assert ctx.context == context_4x4
        assert ctx.step_count == 0
        assert ctx.start_time is not None

    def test_ae_engine_next_step(self, context_4x4):
        """Test AE engine next_step()."""
        engine = NextClosureAEEngine()
        ctx = engine.initialize(context_4x4)

        # Get first concept
        result = engine.next_step(ctx)

        assert isinstance(result, AEResult)
        assert result.success
        assert result.concept is not None
        assert result.statistics.concepts_generated == 1
        assert result.elapsed_time > 0

    def test_ae_engine_multiple_steps(self, context_4x4):
        """Test multiple AE engine steps."""
        engine = NextClosureAEEngine()
        ctx = engine.initialize(context_4x4)

        concepts = []
        for _ in range(5):  # Get first 5 concepts
            result = engine.next_step(ctx)
            if result.success and result.concept is not None:
                concepts.append(result.concept)
            else:
                break

        assert len(concepts) > 0, "No concepts generated"
        assert ctx.step_count == len(concepts)

    def test_ae_engine_statistics(self, context_4x4):
        """Test AE engine statistics."""
        engine = NextClosureAEEngine()
        ctx = engine.initialize(context_4x4)

        # Generate some concepts
        for _ in range(3):
            result = engine.next_step(ctx)
            if not result.success:
                break

        stats = engine.get_statistics()
        assert stats.concepts_generated > 0
        assert stats.elapsed_time > 0
        assert stats.concepts_per_second > 0

    def test_ae_engine_reset(self, context_4x4):
        """Test AE engine reset."""
        engine = NextClosureAEEngine()
        ctx = engine.initialize(context_4x4)

        # Generate some concepts
        for _ in range(3):
            engine.next_step(ctx)

        # Reset and check
        engine.reset()
        stats = engine.get_statistics()
        assert stats.concepts_generated == 0
        assert stats.elapsed_time == 0


class TestConceptLattice:
    """Test concept lattice operations."""

    def test_concept_lattice_creation(self, context_4x4):
        """Test concept lattice creation."""
        next_closure = NextClosure(context_4x4)
        concepts = list(next_closure.generate_concepts())
        lattice = ConceptLattice(concepts)

        assert len(lattice) == len(concepts)
        assert lattice.get_bottom_concept() is not None
        assert lattice.get_top_concept() is not None

    def test_subconcept_relations(self, context_4x4):
        """Test subconcept relations."""
        next_closure = NextClosure(context_4x4)
        concepts = list(next_closure.generate_concepts())
        lattice = ConceptLattice(concepts)

        # Test subconcept relations
        for concept in concepts:
            subconcepts = lattice.get_subconcepts(concept)
            for subconcept in subconcepts:
                assert subconcept.extent.is_subset(concept.extent), "Subconcept relation violated"

    def test_superconcept_relations(self, context_4x4):
        """Test superconcept relations."""
        next_closure = NextClosure(context_4x4)
        concepts = list(next_closure.generate_concepts())
        lattice = ConceptLattice(concepts)

        # Test superconcept relations
        for concept in concepts:
            superconcepts = lattice.get_superconcepts(concept)
            for superconcept in superconcepts:
                assert concept.extent.is_subset(
                    superconcept.extent
                ), "Superconcept relation violated"


class TestPropertyBased:
    """Property-based tests using hypothesis."""

    def test_closure_properties_random(self):
        """Test closure properties on random contexts."""
        # This would use hypothesis for property-based testing
        # For now, we'll test on known contexts

        # Create a simple context
        objects = [Object("a"), Object("b")]
        attributes = [Attribute("x"), Attribute("y")]
        incidence = {
            (objects[0], attributes[0]): True,
            (objects[0], attributes[1]): False,
            (objects[1], attributes[0]): False,
            (objects[1], attributes[1]): True,
        }
        context = FormalContext(objects, attributes, incidence)

        # Test closure properties
        test_intents = [
            Intent(set()),
            Intent({attributes[0]}),
            Intent({attributes[1]}),
            Intent({attributes[0], attributes[1]}),
        ]

        for intent in test_intents:
            # Idempotence
            closed_once = closure(context, intent)
            closed_twice = closure(context, closed_once)
            assert closed_once == closed_twice

            # Extensiveness
            assert intent.is_subset(closed_once)

    def test_lectic_order_properties(self):
        """Test lectic order properties."""
        attributes = [Attribute("a"), Attribute("b"), Attribute("c")]
        attribute_order = attributes

        # Test reflexivity
        intent = Intent({attributes[0]})
        assert lectic_leq(intent, intent, attribute_order)

        # Test transitivity
        intent1 = Intent({attributes[0]})
        intent2 = Intent({attributes[0], attributes[1]})
        intent3 = Intent({attributes[0], attributes[1], attributes[2]})

        assert lectic_leq(intent1, intent2, attribute_order)
        assert lectic_leq(intent2, intent3, attribute_order)
        assert lectic_leq(intent1, intent3, attribute_order)


class TestPerformance:
    """Performance tests."""

    def test_performance_4x4(self, context_4x4):
        """Test performance on 4×4 context."""
        start_time = time.time()

        next_closure = NextClosure(context_4x4)
        concepts = list(next_closure.generate_concepts())

        elapsed_time = time.time() - start_time

        # Should complete quickly
        assert elapsed_time < 0.1, f"Performance test failed: {elapsed_time:.3f}s"
        assert len(concepts) > 0, "No concepts generated"

    def test_performance_5x3(self, context_5x3):
        """Test performance on 5×3 context (< 100ms)."""
        start_time = time.time()

        next_closure = NextClosure(context_5x3)
        concepts = list(next_closure.generate_concepts())

        elapsed_time = time.time() - start_time

        # Should complete in less than 100ms
        assert elapsed_time < 0.1, f"Performance test failed: {elapsed_time:.3f}s > 100ms"
        assert len(concepts) > 0, "No concepts generated"

    def test_performance_fruits(self, context_fruits):
        """Test performance on fruits context."""
        start_time = time.time()

        next_closure = NextClosure(context_fruits)
        concepts = list(next_closure.generate_concepts())

        elapsed_time = time.time() - start_time

        # Should complete quickly
        assert elapsed_time < 0.1, f"Performance test failed: {elapsed_time:.3f}s"
        assert len(concepts) > 0, "No concepts generated"
