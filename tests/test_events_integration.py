"""
Integration smoke test for AE/CEGIS event emissions using MemorySink.
"""

import asyncio
import uuid

from orchestrator.engines.cegis_async_engine import AsyncCegisEngine
from orchestrator.engines.cegis_engine import CegisContext, Verdict
from orchestrator.engines.next_closure_engine import (AEContext,
                                                      NextClosureEngine)
from pefc.events import (EventBusConfig, MemorySink, StructuredEventBus,
                         get_event_bus)


async def _run_smoke():
    # Setup event bus with memory sink
    config = EventBusConfig(buffer_size=128, sinks=["memory"])
    bus = StructuredEventBus(config=config)
    bus.add_sink(MemorySink())
    await bus.start()
    bus.set_correlation_ids(
        trace_id=f"t-{uuid.uuid4().hex[:8]}", run_id=f"r-{uuid.uuid4().hex[:8]}"
    )

    # Minimal AE engine and context
    ae = NextClosureEngine()
    ae.event_bus = bus
    await ae.initialize({"objects": ["o1"], "attributes": ["a1"], "incidence": {}})
    ae_ctx = AEContext(
        run_id="r-test",
        step_id="s-ae",
        trace_id="t-test",
        domain_spec={},
        state={},
        budgets={},
        thresholds={},
    )
    await ae.next_closure_step(ae_ctx)

    # Minimal CEGIS engine and context (mock adapters)
    class _LLM:
        async def generate(self, *args, **kwargs):
            return {"name": "spec", "constraints": [], "properties": []}

    class _Verifier:
        async def verify(self, specification, implementation, constraints):
            return {"valid": True, "confidence": 0.9, "evidence": {}, "metrics": {}}

    cegis = AsyncCegisEngine(_LLM(), _Verifier())
    cegis.event_bus = bus
    await cegis.initialize({})
    c_ctx = CegisContext(
        run_id="r-test",
        step_id="s-cegis",
        trace_id="t-test",
        specification={"name": "spec"},
        constraints=[],
        budgets={"verify_timeout": 5.0},
        state={},
    )
    cand = await cegis.propose(c_ctx)
    res = await cegis.verify(cand, c_ctx)
    assert isinstance(res, (Verdict,)) and res.valid

    # Collect events
    await bus.flush(1.0)
    memory = None
    for s in bus.sinks:
        if isinstance(s, MemorySink):
            memory = s
            break
    assert memory is not None
    events = memory.get_events()

    # Ensure key types present
    types = {e.get("type") for e in events}
    assert "AE.Step" in types
    assert "AE.Concept.Emitted" in types
    assert "CEGIS.Iter.Start" in types
    assert "Verify.Attempt" in types
    assert "Verify.Result" in types

    await bus.stop()


def test_events_smoke():
    asyncio.run(_run_smoke())
    # Minimal post-asserts only for smoke


def test_pipeline_events_simulation():
    """Test simulation of pipeline events."""
    bus = get_event_bus()
    bus.clear()  # Start fresh
    sink = MemorySink()
    bus.subscribe("pipeline.*", sink.handler)

    # Simulate pipeline execution
    bus.emit("pipeline.step.started", step="validate")
    bus.emit("pipeline.step.succeeded", step="validate")
    bus.emit("pipeline.step.started", step="build")
    bus.emit("pipeline.step.succeeded", step="build")

    # Check events were captured
    assert len(sink.events) == 4
    topics = [ev.topic for ev in sink.events]
    assert "pipeline.step.started" in topics
    assert "pipeline.step.succeeded" in topics


def test_capability_events_simulation():
    """Test simulation of capability events."""
    bus = get_event_bus()
    bus.clear()  # Start fresh
    sink = MemorySink()
    bus.subscribe("capability.*", sink.handler)

    # Simulate capability execution
    bus.emit("capability.started", name="opa-proof", req_meta={"type": "policy"})
    bus.emit("capability.succeeded", name="opa-proof", artifacts=["proof.json"])

    # Check events were captured
    assert len(sink.events) == 2
    topics = [ev.topic for ev in sink.events]
    assert "capability.started" in topics
    assert "capability.succeeded" in topics


def test_pack_build_events_simulation():
    """Test simulation of pack build events."""
    bus = get_event_bus()
    bus.clear()  # Start fresh
    sink = MemorySink()
    bus.subscribe("*", sink.handler)

    # Simulate pack build process
    bus.emit("metrics.summary.built", out_path="summary.json", runs=5, version="v0.1.0")
    bus.emit("pack.built", zip="pack.zip", merkle_root="abc123", manifest=True)
    bus.emit("sign.ok", zip="pack.zip", sig="pack.sig", provider="sha256")

    # Check events were captured
    assert len(sink.events) == 3
    topics = [ev.topic for ev in sink.events]
    assert "metrics.summary.built" in topics
    assert "pack.built" in topics
    assert "sign.ok" in topics


def test_error_events_simulation():
    """Test simulation of error events."""
    bus = get_event_bus()
    bus.clear()  # Start fresh
    sink = MemorySink()
    bus.subscribe("*", sink.handler)

    # Simulate error scenarios
    bus.emit("pipeline.step.failed", step="build", error="Build failed")
    bus.emit("capability.failed", name="opa-proof", error="Policy not found")
    bus.emit("sign.fail", zip="pack.zip", error="Signature failed", provider="sha256")

    # Check events were captured
    assert len(sink.events) == 3
    topics = [ev.topic for ev in sink.events]
    assert "pipeline.step.failed" in topics
    assert "capability.failed" in topics
    assert "sign.fail" in topics


def test_mixed_events_priority():
    """Test mixed events with different priorities."""
    bus = get_event_bus()
    bus.clear()  # Start fresh
    results = []

    def high_priority_handler(ev):
        results.append(f"high:{ev.topic}")

    def low_priority_handler(ev):
        results.append(f"low:{ev.topic}")

    bus.subscribe("*", high_priority_handler)
    bus.subscribe("*", low_priority_handler)

    bus.emit("test.event", data="test")

    # High priority should be called first
    assert results == ["high:test.event", "low:test.event"]
