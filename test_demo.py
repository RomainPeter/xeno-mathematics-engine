#!/usr/bin/env python3
"""
Test script to validate the industrialised orchestrator demo.
"""

import asyncio
import shutil
import tempfile
from pathlib import Path

from demo_orchestrator import (DemoLLMAdapter, DemoVerifier,
                               create_demo_budgets, create_demo_domain_spec,
                               create_demo_thresholds)
from orchestrator.config import OrchestratorConfig
from orchestrator.engines.cegis_async_engine import AsyncCegisEngine
from orchestrator.engines.next_closure_engine import NextClosureEngine
from orchestrator.orchestrator import Orchestrator
from pefc.events.structured_bus import StructuredEventBus


async def test_demo_components():
    """Test demo components."""
    print("🧪 Test des composants de démonstration...")

    # Test LLM adapter
    llm = DemoLLMAdapter()
    response = await llm.generate("test prompt")
    assert "candidate_1" in response
    print("✅ LLM Adapter: OK")

    # Test verifier
    verifier = DemoVerifier(success_rate=0.5)
    result = await verifier.verify({}, {}, [])
    assert "valid" in result
    print("✅ Verifier: OK")

    # Test domain spec
    domain_spec = create_demo_domain_spec()
    assert domain_spec["id"] == "demo_regtech"
    assert len(domain_spec["objects"]) == 5
    assert len(domain_spec["attributes"]) == 5
    print("✅ Domain Spec: OK")

    # Test budgets
    budgets = create_demo_budgets()
    assert budgets["ae_timeout"] == 30.0
    assert budgets["total_budget"] == 300.0
    print("✅ Budgets: OK")

    # Test thresholds
    thresholds = create_demo_thresholds()
    assert thresholds["min_confidence"] == 0.8
    assert thresholds["max_iterations"] == 10
    print("✅ Thresholds: OK")


async def test_orchestrator_integration():
    """Test orchestrator integration."""
    print("\n🧪 Test d'intégration de l'orchestrateur...")

    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="test_orchestrator_")

    try:
        # Create configuration
        config = OrchestratorConfig(
            ae_timeout=5.0,
            cegis_propose_timeout=3.0,
            cegis_verify_timeout=3.0,
            cegis_refine_timeout=3.0,
            cegis_max_iterations=3,
            audit_dir=temp_dir,
        )

        # Create components
        llm_adapter = DemoLLMAdapter()
        verifier = DemoVerifier(success_rate=0.8)
        event_bus = StructuredEventBus()

        # Create engines
        ae_engine = NextClosureEngine()
        cegis_engine = AsyncCegisEngine(llm_adapter, verifier)

        # Create orchestrator
        orchestrator = Orchestrator(
            config=config,
            ae_engine=ae_engine,
            cegis_engine=cegis_engine,
            llm_adapter=llm_adapter,
            verifier=verifier,
            event_bus=event_bus,
        )

        # Create test domain spec
        domain_spec = {
            "id": "test_domain",
            "objects": ["obj1", "obj2", "obj3"],
            "attributes": ["attr1", "attr2", "attr3"],
            "specification": {"requirements": ["req1"]},
            "constraints": [{"type": "test", "condition": "test"}],
        }

        budgets = {"ae_timeout": 5.0, "cegis_timeout": 10.0}
        thresholds = {"min_confidence": 0.8, "max_iterations": 3}

        # Track events
        events = []

        def event_handler(event):
            events.append(event)

        event_bus.subscribe("*", event_handler)

        # Run orchestrator
        print("🔄 Exécution de l'orchestrateur...")
        state = await orchestrator.run(domain_spec, budgets, thresholds)

        # Verify results
        assert state.run_id is not None
        assert state.trace_id is not None
        assert state.phase in ["completed", "failed"]
        print(f"✅ Orchestrateur exécuté: {state.phase}")

        # Verify events
        assert len(events) > 0
        event_types = [event.topic for event in events]
        assert "orchestrator.started" in event_types
        print(f"✅ Événements publiés: {len(events)}")

        # Verify audit pack
        audit_dir = Path(temp_dir)
        packs_dir = audit_dir / "packs" / state.run_id

        if packs_dir.exists():
            assert (packs_dir / "manifest.json").exists()
            assert (packs_dir / "pcaps.json").exists()
            assert (packs_dir / "incidents.json").exists()
            print("✅ Audit pack créé")

        print("📊 Résultats:")
        print(f"   - AE: {len(state.ae_results)} étapes")
        print(f"   - CEGIS: {len(state.cegis_results)} itérations")
        print(f"   - Incidents: {len(state.incidents)}")
        print(f"   - Événements: {len(events)}")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_next_closure_engine():
    """Test Next-Closure engine."""
    print("\n🧪 Test du moteur Next-Closure...")

    engine = NextClosureEngine()

    # Initialize
    domain_spec = {
        "objects": ["obj1", "obj2", "obj3"],
        "attributes": ["attr1", "attr2", "attr3"],
    }

    await engine.initialize(domain_spec)
    assert engine.initialized
    print("✅ Initialisation: OK")

    # Test context creation
    context = engine._build_formal_context(domain_spec)
    assert context.objects == ["obj1", "obj2", "obj3"]
    assert context.attributes == ["attr1", "attr2", "attr3"]
    assert len(context.incidence) == 9  # 3x3
    print("✅ Contexte formel: OK")

    # Test extent computation
    extent = await engine._compute_extent({"attr1", "attr2"})
    assert isinstance(extent, set)
    print("✅ Calcul d'étendue: OK")

    # Test intent computation
    intent = await engine._compute_intent({"obj1", "obj2"})
    assert isinstance(intent, set)
    print("✅ Calcul d'intention: OK")

    await engine.cleanup()
    assert not engine.initialized
    print("✅ Nettoyage: OK")


async def test_cegis_engine():
    """Test CEGIS engine."""
    print("\n🧪 Test du moteur CEGIS...")

    llm_adapter = DemoLLMAdapter()
    verifier = DemoVerifier(success_rate=0.7)
    engine = AsyncCegisEngine(llm_adapter, verifier)

    # Initialize
    domain_spec = {
        "specification": {"requirements": ["req1"]},
        "constraints": [{"type": "test", "condition": "test"}],
    }

    await engine.initialize(domain_spec)
    assert engine.initialized
    print("✅ Initialisation: OK")

    # Test candidate generation
    from orchestrator.engines.cegis_engine import CegisContext

    ctx = CegisContext(
        run_id="test",
        step_id="step1",
        trace_id="trace1",
        specification={"requirements": ["req1"]},
        constraints=[{"type": "test"}],
        budgets={},
        state={},
    )

    candidate = await engine.propose(ctx)
    assert candidate.id is not None
    assert candidate.specification is not None
    assert candidate.implementation is not None
    print("✅ Génération de candidat: OK")

    # Test verification
    result = await engine.verify(candidate, ctx)
    assert hasattr(result, "valid") or hasattr(result, "failing_property")
    print("✅ Vérification: OK")

    await engine.cleanup()
    assert not engine.initialized
    print("✅ Nettoyage: OK")


async def run_all_tests():
    """Run all tests."""
    print("🧪 TESTS DE VALIDATION - ORCHESTRATEUR INDUSTRIALISÉ")
    print("=" * 60)

    try:
        await test_demo_components()
        await test_next_closure_engine()
        await test_cegis_engine()
        await test_orchestrator_integration()

        print("\n✅ TOUS LES TESTS RÉUSSIS")
        print("🎯 L'orchestrateur industrialisé est prêt pour la démonstration")

    except Exception as e:
        print(f"\n❌ ÉCHEC DES TESTS: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())
