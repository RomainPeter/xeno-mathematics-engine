from __future__ import annotations
from pefc.events.subscribers import PrometheusStub
from pefc.events.bus import EventBus


def test_prometheus_stub_counting():
    """Test Prometheus stub event counting."""
    stub = PrometheusStub()
    bus = EventBus()
    bus.subscribe("*", stub.handler)

    # Emit various events
    bus.emit("pack.built", zip="test.zip")
    bus.emit("pack.built", zip="test2.zip")
    bus.emit("pipeline.step.started", step="A")
    bus.emit("pipeline.step.succeeded", step="A")
    bus.emit("capability.started", name="test")

    # Check counts
    assert stub.counts["pack.built"] == 2
    assert stub.counts["pipeline.step.started"] == 1
    assert stub.counts["pipeline.step.succeeded"] == 1
    assert stub.counts["capability.started"] == 1


def test_prometheus_stub_empty_counts():
    """Test Prometheus stub with no events."""
    stub = PrometheusStub()
    assert stub.counts == {}


def test_prometheus_stub_multiple_handlers():
    """Test Prometheus stub with multiple handlers."""
    stub1 = PrometheusStub()
    stub2 = PrometheusStub()
    bus = EventBus()
    bus.subscribe("*", stub1.handler)
    bus.subscribe("*", stub2.handler)

    bus.emit("test.event", data="test")

    # Both stubs should count the event
    assert stub1.counts["test.event"] == 1
    assert stub2.counts["test.event"] == 1


def test_prometheus_stub_wildcard_filtering():
    """Test Prometheus stub with wildcard filtering."""
    stub = PrometheusStub()
    bus = EventBus()
    bus.subscribe("pipeline.*", stub.handler)

    bus.emit("pipeline.step.started", step="A")
    bus.emit("pipeline.step.succeeded", step="A")
    bus.emit("pack.built", zip="test.zip")
    bus.emit("capability.started", name="test")

    # Only pipeline events should be counted
    assert stub.counts["pipeline.step.started"] == 1
    assert stub.counts["pipeline.step.succeeded"] == 1
    assert "pack.built" not in stub.counts
    assert "capability.started" not in stub.counts


def test_prometheus_stub_reset():
    """Test Prometheus stub count reset."""
    stub = PrometheusStub()
    bus = EventBus()
    bus.subscribe("*", stub.handler)

    bus.emit("test.event", data="test")
    assert stub.counts["test.event"] == 1

    # Reset counts
    stub.counts.clear()
    assert stub.counts == {}

    bus.emit("test.event", data="test")
    assert stub.counts["test.event"] == 1
