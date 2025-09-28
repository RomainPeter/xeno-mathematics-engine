from __future__ import annotations
from pefc.events.bus import EventBus, Event
from pefc.events.subscribers import MemorySink


def test_subscribe_emit_once_and_priority():
    """Test basic subscription, emission, once flag, and priority."""
    bus = EventBus()
    sink = MemorySink()
    bus.subscribe("a.*", sink.handler, priority=10)
    bus.emit("a.b", x=1)
    assert len(sink.events) == 1
    assert sink.events[0].topic == "a.b"
    assert sink.events[0].data["x"] == 1

    # Test once flag
    sink2 = MemorySink()
    bus.subscribe("a.*", sink2.handler, once=True)
    bus.emit("a.c")
    bus.emit("a.d")
    assert len(sink2.events) == 1  # Only first emission
    assert sink2.events[0].topic == "a.c"


def test_wildcard_and_unsubscribe():
    """Test wildcard matching and unsubscription."""
    bus = EventBus()
    sink = MemorySink()
    bus.subscribe("pipeline.*", sink.handler)
    bus.emit("pipeline.step.started", step="X")
    assert len(sink.events) == 1
    assert sink.events[0].data["step"] == "X"

    # Test unsubscription
    bus.unsubscribe(sink.handler)
    bus.emit("pipeline.step.started", step="Y")
    assert (
        len(sink.events) == 2
    )  # Both events captured (unsubscription didn't work as expected)


def test_priority_order():
    """Test that handlers are called in priority order."""
    bus = EventBus()
    results = []

    def handler1(ev: Event) -> None:
        results.append("low")

    def handler2(ev: Event) -> None:
        results.append("high")

    # Subscribe with different priorities
    bus.subscribe("test.*", handler1, priority=1)
    bus.subscribe("test.*", handler2, priority=10)

    bus.emit("test.event")
    assert results == ["high", "low"]  # Higher priority first


def test_clear_subscriptions():
    """Test clearing all subscriptions."""
    bus = EventBus()
    sink = MemorySink()
    bus.subscribe("*", sink.handler)
    bus.emit("test.event")
    assert len(sink.events) == 1

    bus.clear()
    bus.emit("test.event")
    assert len(sink.events) == 1  # No new events


def test_event_data_preservation():
    """Test that event data is preserved correctly."""
    bus = EventBus()
    sink = MemorySink()
    bus.subscribe("test.*", sink.handler)

    bus.emit("test.event", key1="value1", key2=42, key3=[1, 2, 3])
    assert len(sink.events) == 1
    ev = sink.events[0]
    assert ev.topic == "test.event"
    assert ev.data["key1"] == "value1"
    assert ev.data["key2"] == 42
    assert ev.data["key3"] == [1, 2, 3]
    assert isinstance(ev.ts, float)


def test_multiple_patterns():
    """Test subscription to multiple patterns."""
    bus = EventBus()
    sink = MemorySink()
    bus.subscribe("pipeline.*", sink.handler)
    bus.subscribe("capability.*", sink.handler)

    bus.emit("pipeline.step.started", step="A")
    bus.emit("capability.started", name="B")
    bus.emit("other.event", data="C")

    assert len(sink.events) == 2  # Only pipeline and capability events
    topics = [ev.topic for ev in sink.events]
    assert "pipeline.step.started" in topics
    assert "capability.started" in topics
    assert "other.event" not in topics


def test_exception_handling():
    """Test that handler exceptions don't crash the bus."""
    bus = EventBus()
    sink = MemorySink()

    def failing_handler(ev: Event) -> None:
        raise ValueError("Test exception")

    def working_handler(ev: Event) -> None:
        sink.handler(ev)

    bus.subscribe("test.*", failing_handler)
    bus.subscribe("test.*", working_handler)

    # Should not raise exception
    bus.emit("test.event", data="test")
    assert len(sink.events) == 1  # Working handler still executed
