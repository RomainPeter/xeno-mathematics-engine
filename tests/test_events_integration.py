from __future__ import annotations
from pefc.events.subscribers import MemorySink
from pefc.events import get_event_bus
from pefc.events import topics as E


def test_singleton_event_bus():
    """Test that get_event_bus returns singleton."""
    bus1 = get_event_bus()
    bus2 = get_event_bus()
    assert bus1 is bus2


def test_event_bus_clear():
    """Test clearing the singleton event bus."""
    bus = get_event_bus()
    sink = MemorySink()
    bus.subscribe("*", sink.handler)
    bus.emit("test.event", data="test")
    assert len(sink.events) == 1

    bus.clear()
    bus.emit("test.event", data="test")
    assert len(sink.events) == 1  # No new events after clear


def test_topics_constants():
    """Test that topic constants are defined."""
    assert E.RUN_FINISHED == "run.finished"
    assert E.INCIDENT_RAISED == "incident.raised"
    assert E.PACK_BUILT == "pack.built"
    assert E.PIPELINE_STEP_STARTED == "pipeline.step.started"
    assert E.PIPELINE_STEP_SUCCEEDED == "pipeline.step.succeeded"
    assert E.PIPELINE_STEP_FAILED == "pipeline.step.failed"
    assert E.CAPABILITY_STARTED == "capability.started"
    assert E.CAPABILITY_SUCCEEDED == "capability.succeeded"
    assert E.CAPABILITY_FAILED == "capability.failed"
    assert E.METRICS_SUMMARY_BUILT == "metrics.summary.built"
    assert E.SIGN_OK == "sign.ok"
    assert E.SIGN_FAIL == "sign.fail"


def test_pipeline_events_simulation():
    """Test simulation of pipeline events."""
    bus = get_event_bus()
    bus.clear()  # Start fresh
    sink = MemorySink()
    bus.subscribe("pipeline.*", sink.handler)

    # Simulate pipeline execution
    bus.emit(E.PIPELINE_STEP_STARTED, step="validate")
    bus.emit(E.PIPELINE_STEP_SUCCEEDED, step="validate")
    bus.emit(E.PIPELINE_STEP_STARTED, step="build")
    bus.emit(E.PIPELINE_STEP_SUCCEEDED, step="build")

    # Check events were captured
    assert len(sink.events) == 4
    topics = [ev.topic for ev in sink.events]
    assert E.PIPELINE_STEP_STARTED in topics
    assert E.PIPELINE_STEP_SUCCEEDED in topics


def test_capability_events_simulation():
    """Test simulation of capability events."""
    bus = get_event_bus()
    bus.clear()  # Start fresh
    sink = MemorySink()
    bus.subscribe("capability.*", sink.handler)

    # Simulate capability execution
    bus.emit(E.CAPABILITY_STARTED, name="opa-proof", req_meta={"type": "policy"})
    bus.emit(E.CAPABILITY_SUCCEEDED, name="opa-proof", artifacts=["proof.json"])

    # Check events were captured
    assert len(sink.events) == 2
    topics = [ev.topic for ev in sink.events]
    assert E.CAPABILITY_STARTED in topics
    assert E.CAPABILITY_SUCCEEDED in topics


def test_pack_build_events_simulation():
    """Test simulation of pack build events."""
    bus = get_event_bus()
    bus.clear()  # Start fresh
    sink = MemorySink()
    bus.subscribe("*", sink.handler)

    # Simulate pack build process
    bus.emit(E.METRICS_SUMMARY_BUILT, out_path="summary.json", runs=5, version="v0.1.0")
    bus.emit(E.PACK_BUILT, zip="pack.zip", merkle_root="abc123", manifest=True)
    bus.emit(E.SIGN_OK, zip="pack.zip", sig="pack.sig", provider="sha256")

    # Check events were captured
    assert len(sink.events) == 3
    topics = [ev.topic for ev in sink.events]
    assert E.METRICS_SUMMARY_BUILT in topics
    assert E.PACK_BUILT in topics
    assert E.SIGN_OK in topics


def test_error_events_simulation():
    """Test simulation of error events."""
    bus = get_event_bus()
    bus.clear()  # Start fresh
    sink = MemorySink()
    bus.subscribe("*", sink.handler)

    # Simulate error scenarios
    bus.emit(E.PIPELINE_STEP_FAILED, step="build", error="Build failed")
    bus.emit(E.CAPABILITY_FAILED, name="opa-proof", error="Policy not found")
    bus.emit(E.SIGN_FAIL, zip="pack.zip", error="Signature failed", provider="sha256")

    # Check events were captured
    assert len(sink.events) == 3
    topics = [ev.topic for ev in sink.events]
    assert E.PIPELINE_STEP_FAILED in topics
    assert E.CAPABILITY_FAILED in topics
    assert E.SIGN_FAIL in topics


def test_mixed_events_priority():
    """Test mixed events with different priorities."""
    bus = get_event_bus()
    bus.clear()  # Start fresh
    results = []

    def high_priority_handler(ev):
        results.append(f"high:{ev.topic}")

    def low_priority_handler(ev):
        results.append(f"low:{ev.topic}")

    bus.subscribe("*", high_priority_handler, priority=10)
    bus.subscribe("*", low_priority_handler, priority=1)

    bus.emit("test.event", data="test")

    # High priority should be called first
    assert results == ["high:test.event", "low:test.event"]
