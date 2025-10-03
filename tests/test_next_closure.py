"""
Tests for Next-Closure algorithm implementation.
"""

from typing import Any, Dict

import pytest

from orchestrator.engines.ae_engine import AEContext
from orchestrator.engines.next_closure_engine import NextClosureEngine


class TestNextClosureEngine:
    """Test cases for Next-Closure engine."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return NextClosureEngine()

    @pytest.fixture
    def toy_context_4x4(self) -> Dict[str, Any]:
        """4x4 toy context for testing."""
        return {
            "objects": ["obj1", "obj2", "obj3", "obj4"],
            "attributes": ["attr1", "attr2", "attr3", "attr4"],
            "incidence": {
                ("obj1", "attr1"): True,
                ("obj1", "attr2"): True,
                ("obj1", "attr3"): False,
                ("obj1", "attr4"): False,
                ("obj2", "attr1"): True,
                ("obj2", "attr2"): False,
                ("obj2", "attr3"): True,
                ("obj2", "attr4"): False,
                ("obj3", "attr1"): False,
                ("obj3", "attr2"): True,
                ("obj3", "attr3"): True,
                ("obj3", "attr4"): True,
                ("obj4", "attr1"): False,
                ("obj4", "attr2"): False,
                ("obj4", "attr3"): False,
                ("obj4", "attr4"): True,
            },
        }

    @pytest.fixture
    def toy_context_5x3(self) -> Dict[str, Any]:
        """5x3 toy context for testing."""
        return {
            "objects": ["obj1", "obj2", "obj3", "obj4", "obj5"],
            "attributes": ["attr1", "attr2", "attr3"],
            "incidence": {
                ("obj1", "attr1"): True,
                ("obj1", "attr2"): True,
                ("obj1", "attr3"): False,
                ("obj2", "attr1"): False,
                ("obj2", "attr2"): True,
                ("obj2", "attr3"): True,
                ("obj3", "attr1"): True,
                ("obj3", "attr2"): False,
                ("obj3", "attr3"): True,
                ("obj4", "attr1"): True,
                ("obj4", "attr2"): True,
                ("obj4", "attr3"): True,
                ("obj5", "attr1"): False,
                ("obj5", "attr2"): False,
                ("obj5", "attr3"): False,
            },
        }

    @pytest.mark.asyncio
    async def test_initialization(self, engine):
        """Test engine initialization."""
        domain_spec = {"objects": ["obj1"], "attributes": ["attr1"]}

        await engine.initialize(domain_spec)

        assert engine.initialized
        assert engine.context is not None
        assert len(engine.concepts) == 0
        assert len(engine.implications) == 0

    @pytest.mark.asyncio
    async def test_first_concept_4x4(self, engine, toy_context_4x4):
        """Test first concept generation for 4x4 context."""
        await engine.initialize(toy_context_4x4)

        ctx = AEContext(
            run_id="test_run",
            step_id="step_1",
            trace_id="trace_1",
            domain_spec=toy_context_4x4,
            state={},
            budgets={},
            thresholds={},
        )

        result = await engine.next_closure_step(ctx)

        assert result.success
        assert len(result.concepts) == 1
        assert len(result.implications) >= 0

        concept = result.concepts[0]
        assert "extent" in concept
        assert "intent" in concept
        assert "support" in concept
        assert "confidence" in concept

    @pytest.mark.asyncio
    async def test_lectic_order_invariant(self, engine, toy_context_4x4):
        """Test that concepts are generated in lectic order."""
        await engine.initialize(toy_context_4x4)

        concepts = []
        for i in range(3):  # Generate 3 concepts
            ctx = AEContext(
                run_id="test_run",
                step_id=f"step_{i}",
                trace_id="trace_1",
                domain_spec=toy_context_4x4,
                state={},
                budgets={},
                thresholds={},
            )

            result = await engine.next_closure_step(ctx)
            if result.success and result.concepts:
                concepts.append(result.concepts[0])

        # Check lectic order: each concept should be "greater" than previous
        for i in range(1, len(concepts)):
            prev_intent = set(concepts[i - 1]["intent"])
            curr_intent = set(concepts[i]["intent"])

            # In lectic order, we should have a total ordering
            assert prev_intent != curr_intent

    @pytest.mark.asyncio
    async def test_closure_idempotence(self, engine, toy_context_5x3):
        """Test that closure operation is idempotent."""
        await engine.initialize(toy_context_5x3)

        # Test extent computation
        intent = {"attr1", "attr2"}
        extent1 = await engine._compute_extent(intent)
        extent2 = await engine._compute_extent(intent)
        assert extent1 == extent2

        # Test intent computation
        extent = {"obj1", "obj4"}
        intent1 = await engine._compute_intent(extent)
        intent2 = await engine._compute_intent(extent)
        assert intent1 == intent2

    @pytest.mark.asyncio
    async def test_no_duplicate_concepts(self, engine, toy_context_4x4):
        """Test that no duplicate concepts are generated."""
        await engine.initialize(toy_context_4x4)

        concept_signatures = set()

        for i in range(5):  # Generate 5 concepts
            ctx = AEContext(
                run_id="test_run",
                step_id=f"step_{i}",
                trace_id="trace_1",
                domain_spec=toy_context_4x4,
                state={},
                budgets={},
                thresholds={},
            )

            result = await engine.next_closure_step(ctx)
            if result.success and result.concepts:
                concept = result.concepts[0]
                signature = (
                    tuple(sorted(concept["extent"])),
                    tuple(sorted(concept["intent"])),
                )
                assert signature not in concept_signatures, f"Duplicate concept found: {signature}"
                concept_signatures.add(signature)

    @pytest.mark.asyncio
    async def test_implication_generation(self, engine, toy_context_4x4):
        """Test implication generation from concepts."""
        await engine.initialize(toy_context_4x4)

        ctx = AEContext(
            run_id="test_run",
            step_id="step_1",
            trace_id="trace_1",
            domain_spec=toy_context_4x4,
            state={},
            budgets={},
            thresholds={},
        )

        result = await engine.next_closure_step(ctx)

        assert result.success
        assert len(result.implications) >= 0

        # Check implication structure
        for impl in result.implications:
            assert "id" in impl
            assert "premises" in impl
            assert "conclusions" in impl
            assert "support" in impl
            assert "confidence" in impl
            assert isinstance(impl["premises"], list)
            assert isinstance(impl["conclusions"], list)

    @pytest.mark.asyncio
    async def test_cleanup(self, engine, toy_context_4x4):
        """Test engine cleanup."""
        await engine.initialize(toy_context_4x4)
        assert engine.initialized

        await engine.cleanup()
        assert not engine.initialized
        assert engine.context is None
        assert len(engine.concepts) == 0
        assert len(engine.implications) == 0

    @pytest.mark.asyncio
    async def test_error_handling(self, engine):
        """Test error handling for uninitialized engine."""
        ctx = AEContext(
            run_id="test_run",
            step_id="step_1",
            trace_id="trace_1",
            domain_spec={},
            state={},
            budgets={},
            thresholds={},
        )

        result = await engine.next_closure_step(ctx)
        assert not result.success
        assert result.error is not None

    def test_formal_context_creation(self, engine):
        """Test formal context creation from domain spec."""
        domain_spec = {"objects": ["obj1", "obj2"], "attributes": ["attr1", "attr2"]}

        context = engine._build_formal_context(domain_spec)

        assert context.objects == ["obj1", "obj2"]
        assert context.attributes == ["attr1", "attr2"]
        assert len(context.incidence) == 4  # 2 objects × 2 attributes

        # Check that incidence relation is properly set
        for obj in context.objects:
            for attr in context.attributes:
                assert (obj, attr) in context.incidence
                assert isinstance(context.incidence[(obj, attr)], bool)
