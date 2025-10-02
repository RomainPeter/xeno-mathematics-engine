from __future__ import annotations

import logging

from pefc.events.bus import EventBus
from pefc.events.subscribers import LoggingSubscriber, MemorySink


def test_logging_levels_do_not_crash(caplog):
    """Test that logging subscriber doesn't crash on different event types."""
    bus = EventBus()
    logger = logging.getLogger("pefc.test")
    bus.subscribe("*", LoggingSubscriber(logger).handler)

    # Emit various event types
    bus.emit("pack.built", zip="test.zip")
    bus.emit("pipeline.step.failed", step="A", error="test error")
    bus.emit("capability.succeeded", name="test")

    # Should not raise any exceptions
    assert True


def test_logging_subscriber_error_level(caplog):
    """Test that error events are logged at ERROR level."""
    bus = EventBus()
    logger = logging.getLogger("pefc.test")
    subscriber = LoggingSubscriber(logger)
    bus.subscribe("*", subscriber.handler)

    with caplog.at_level(logging.ERROR):
        bus.emit("pipeline.step.failed", step="test", error="test error")
        bus.emit("capability.failed", name="test", error="test error")

    # Check that error events were logged
    error_logs = [record for record in caplog.records if record.levelno == logging.ERROR]
    assert len(error_logs) >= 1  # At least one error event


def test_logging_subscriber_info_level(caplog):
    """Test that normal events are logged at INFO level."""
    bus = EventBus()
    logger = logging.getLogger("pefc.test")
    subscriber = LoggingSubscriber(logger)
    bus.subscribe("*", subscriber.handler)

    with caplog.at_level(logging.INFO):
        bus.emit("pack.built", zip="test.zip")
        bus.emit("capability.succeeded", name="test")

    # Check that info events were logged
    info_logs = [record for record in caplog.records if record.levelno == logging.INFO]
    assert len(info_logs) >= 1  # At least one info event


def test_logging_subscriber_structured_data(caplog):
    """Test that logging subscriber preserves structured data."""
    bus = EventBus()
    logger = logging.getLogger("pefc.test")
    subscriber = LoggingSubscriber(logger)
    bus.subscribe("*", subscriber.handler)

    with caplog.at_level(logging.INFO):
        bus.emit("test.event", key1="value1", key2=42)

    # Check that structured data is in the log record
    log_record = caplog.records[-1]
    assert log_record.event == "test.event"
    assert log_record.key1 == "value1"
    assert log_record.key2 == 42


def test_memory_sink_basic():
    """Test basic memory sink functionality."""
    sink = MemorySink()
    bus = EventBus()
    bus.subscribe("*", sink.handler)

    bus.emit("test.event", data="test")
    assert len(sink.events) == 1
    assert sink.events[0].topic == "test.event"
    assert sink.events[0].data["data"] == "test"


def test_memory_sink_multiple_events():
    """Test memory sink with multiple events."""
    sink = MemorySink()
    bus = EventBus()
    bus.subscribe("*", sink.handler)

    bus.emit("event1", data="1")
    bus.emit("event2", data="2")
    bus.emit("event3", data="3")

    assert len(sink.events) == 3
    topics = [ev.topic for ev in sink.events]
    assert topics == ["event1", "event2", "event3"]
