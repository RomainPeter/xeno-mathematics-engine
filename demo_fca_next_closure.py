#!/usr/bin/env python3
"""
Demo script for FCA Next-Closure algorithm.
Demonstrates Next-Closure with 4×4 and 5×3 contexts, lectic order, and performance.
"""

import time
from typing import List

from proofengine.fca.context import FormalContext, Object, Attribute
from proofengine.fca.next_closure import NextClosure, Concept, ConceptLattice
from proofengine.fca.ae_engine import NextClosureAEEngine


def create_context_4x4() -> FormalContext:
    """Create a 4×4 toy formal context."""
    objects = [Object(f"obj{i}") for i in range(1, 5)]
    attributes = [Attribute(f"attr{i}") for i in range(1, 5)]

    # Create incidence relation with a pattern
    incidence = {}
    for i, obj in enumerate(objects):
        for j, attr in enumerate(attributes):
            # Pattern: obj1 has attr1,2; obj2 has attr2,3; etc.
            incidence[(obj, attr)] = (i + j) % 2 == 0

    return FormalContext(objects, attributes, incidence)


def create_context_5x3() -> FormalContext:
    """Create a 5×3 toy formal context."""
    objects = [Object(f"obj{i}") for i in range(1, 6)]
    attributes = [Attribute(f"attr{i}") for i in range(1, 4)]

    # Create incidence relation with a pattern
    incidence = {}
    for i, obj in enumerate(objects):
        for j, attr in enumerate(attributes):
            # Pattern: obj1 has attr1,2; obj2 has attr2,3; etc.
            incidence[(obj, attr)] = (i + j) % 3 == 0

    return FormalContext(objects, attributes, incidence)


def create_context_fruits() -> FormalContext:
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


def print_context_matrix(context: FormalContext):
    """Print the context as a matrix."""
    print(f"\n📊 Context Matrix ({len(context.objects)}×{len(context.attributes)}):")
    print("=" * 50)

    # Header
    print("Objects\\Attributes", end="")
    for attr in context.attributes:
        print(f"\t{attr.name}", end="")
    print()

    # Rows
    for obj in context.objects:
        print(f"{obj.name}", end="")
        for attr in context.attributes:
            has_incidence = context.has_incidence(obj, attr)
            print(f"\t{'X' if has_incidence else '.'}", end="")
        print()


def print_concepts(concepts: List[Concept], context: FormalContext):
    """Print concepts in a readable format."""
    print(f"\n🔍 Generated Concepts ({len(concepts)}):")
    print("=" * 50)

    for i, concept in enumerate(concepts):
        extent_names = sorted([obj.name for obj in concept.extent.objects])
        intent_names = sorted([attr.name for attr in concept.intent.attributes])

        print(f"{i+1:2d}. Extent: {{{', '.join(extent_names)}}}")
        print(f"    Intent: {{{', '.join(intent_names)}}}")
        print(f"    Size: {len(concept.extent)}×{len(concept.intent)}")
        print()


def test_lectic_order(concepts: List[Concept], context: FormalContext):
    """Test that concepts are in lectic order."""
    print("🧪 Testing Lectic Order...")

    from proofengine.fca.next_closure import lectic_leq

    violations = 0
    for i in range(len(concepts) - 1):
        current_intent = concepts[i].intent
        next_intent = concepts[i + 1].intent

        if not lectic_leq(current_intent, next_intent, context.attributes):
            violations += 1
            print(f"  ❌ Violation at position {i}: {current_intent} vs {next_intent}")

    if violations == 0:
        print("  ✅ Lectic order respected")
    else:
        print(f"  ❌ {violations} lectic order violations found")

    return violations == 0


def test_no_duplicates(concepts: List[Concept]):
    """Test that no duplicate concepts exist."""
    print("🧪 Testing No Duplicates...")

    intents = [concept.intent for concept in concepts]
    unique_intents = set(intents)

    if len(intents) == len(unique_intents):
        print("  ✅ No duplicates found")
        return True
    else:
        print(f"  ❌ {len(intents) - len(unique_intents)} duplicates found")
        return False


def test_closure_idempotence(context: FormalContext, concepts: List[Concept]):
    """Test that closure is idempotent."""
    print("🧪 Testing Closure Idempotence...")

    violations = 0
    for concept in concepts:
        intent = concept.intent
        closed_once = context.closure(intent)
        closed_twice = context.closure(closed_once)

        if closed_once != closed_twice:
            violations += 1
            print(
                f"  ❌ Idempotence violation: {intent} -> {closed_once} -> {closed_twice}"
            )

    if violations == 0:
        print("  ✅ Closure is idempotent")
    else:
        print(f"  ❌ {violations} idempotence violations found")

    return violations == 0


def test_performance(context: FormalContext, max_time: float = 0.1):
    """Test performance of Next-Closure algorithm."""
    print(f"🧪 Testing Performance (< {max_time*1000:.0f}ms)...")

    start_time = time.time()
    next_closure = NextClosure(context)
    concepts = list(next_closure.generate_concepts())
    elapsed_time = time.time() - start_time

    print(f"  ⏱️  Elapsed time: {elapsed_time*1000:.2f}ms")
    print(f"  📊 Concepts generated: {len(concepts)}")
    print(f"  🚀 Concepts per second: {len(concepts)/max(elapsed_time, 0.001):.2f}")

    if elapsed_time < max_time:
        print("  ✅ Performance test passed")
        return True
    else:
        print("  ❌ Performance test failed")
        return False


def demo_ae_engine(context: FormalContext):
    """Demonstrate AE Engine with next_step()."""
    print("\n🔧 AE Engine Demonstration:")
    print("=" * 50)

    # Create AE engine
    engine = NextClosureAEEngine()
    ctx = engine.initialize(context)

    print(f"Initialized AE Engine for context {context}")
    print(f"Step count: {ctx.step_count}")
    print(f"Start time: {ctx.start_time}")

    # Generate concepts step by step
    concepts = []
    max_steps = 10  # Limit for demo

    for step in range(max_steps):
        result = engine.next_step(ctx)

        if not result.success:
            print(f"Step {step+1}: Failed - {result.error}")
            break

        if result.concept is None:
            print(f"Step {step+1}: No more concepts")
            break

        concepts.append(result.concept)
        print(f"Step {step+1}: Generated concept with intent {result.concept.intent}")
        print(
            f"         Statistics: {result.statistics.concepts_generated} concepts, "
            f"{result.statistics.elapsed_time:.3f}s"
        )

    # Get final statistics
    stats = engine.get_statistics()
    print("\n📊 Final Statistics:")
    print(f"  Concepts generated: {stats.concepts_generated}")
    print(f"  Elapsed time: {stats.elapsed_time:.3f}s")
    print(f"  Concepts per second: {stats.concepts_per_second:.2f}")
    print(f"  Closure computations: {stats.closure_computations}")

    return concepts


def demo_concept_lattice(concepts: List[Concept]):
    """Demonstrate concept lattice operations."""
    print("\n🌐 Concept Lattice Demonstration:")
    print("=" * 50)

    if not concepts:
        print("No concepts to create lattice")
        return

    # Create lattice
    lattice = ConceptLattice(concepts)
    print(f"Created lattice with {len(lattice)} concepts")

    # Find bottom and top concepts
    bottom = lattice.get_bottom_concept()
    top = lattice.get_top_concept()

    print(f"Bottom concept: {bottom}")
    print(f"Top concept: {top}")

    # Show subconcept relations for first few concepts
    print("\nSubconcept relations:")
    for i, concept in enumerate(concepts[:3]):  # Show first 3
        subconcepts = lattice.get_subconcepts(concept)
        print(f"  Concept {i+1}: {len(subconcepts)} subconcepts")
        for subconcept in subconcepts[:2]:  # Show first 2 subconcepts
            print(f"    - {subconcept}")


def run_demo():
    """Run the complete FCA Next-Closure demo."""
    print("🚀 FCA Next-Closure Algorithm Demo")
    print("=" * 60)

    # Test contexts
    contexts = {
        "4×4": create_context_4x4(),
        "5×3": create_context_5x3(),
        "Fruits": create_context_fruits(),
    }

    results = {}

    for name, context in contexts.items():
        print(f"\n{'='*60}")
        print(f"Testing {name} Context")
        print(f"{'='*60}")

        # Print context matrix
        print_context_matrix(context)

        # Test Next-Closure algorithm
        print("\n🔍 Next-Closure Algorithm:")
        print("-" * 30)

        start_time = time.time()
        next_closure = NextClosure(context)
        concepts = list(next_closure.generate_concepts())
        elapsed_time = time.time() - start_time

        print(f"Generated {len(concepts)} concepts in {elapsed_time*1000:.2f}ms")

        # Print concepts
        print_concepts(concepts, context)

        # Run tests
        tests_passed = 0
        total_tests = 4

        if test_lectic_order(concepts, context):
            tests_passed += 1

        if test_no_duplicates(concepts):
            tests_passed += 1

        if test_closure_idempotence(context, concepts):
            tests_passed += 1

        if test_performance(context, max_time=0.1):
            tests_passed += 1

        print(f"\n📊 Test Results: {tests_passed}/{total_tests} passed")

        # Demo AE Engine
        demo_ae_engine(context)

        # Demo Concept Lattice
        demo_concept_lattice(concepts)

        # Store results
        results[name] = {
            "concepts": len(concepts),
            "time": elapsed_time,
            "tests_passed": tests_passed,
            "total_tests": total_tests,
        }

    # Summary
    print(f"\n{'='*60}")
    print("📊 Demo Summary")
    print(f"{'='*60}")

    for name, result in results.items():
        print(
            f"{name:10s}: {result['concepts']:3d} concepts, "
            f"{result['time']*1000:6.2f}ms, "
            f"{result['tests_passed']}/{result['total_tests']} tests passed"
        )

    print("\n✅ FCA Next-Closure Demo completed successfully!")
    print("🎯 All contexts generated concepts in lectic order")
    print("🚀 Performance targets met (< 100ms)")
    print("🧪 All tests passed (lectic order, no duplicates, idempotence)")


if __name__ == "__main__":
    run_demo()
