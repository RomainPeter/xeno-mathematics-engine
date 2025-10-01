#!/usr/bin/env python3
"""
Tests for logging and events functionality.
"""
from unittest.mock import Mock


from pefc.events import EventBus
from pefc.events.subscribers import LoggingSubscriber
from pefc.logging import init_logging, get_logger


class TestEventBus:
    """Test EventBus functionality."""

    def test_event_bus_creation(self):
        """Test EventBus creation."""
        bus = EventBus()

        # Check initial state
        assert len(bus.subscribers) == 0
        assert bus.events == []

    def test_event_bus_subscribe(self):
        """Test event subscription."""
        bus = EventBus()

        # Create mock subscriber
        subscriber = Mock()

        # Subscribe to event
        bus.subscribe("test.event", subscriber.handler)

        # Check subscription
        assert len(bus.subscribers) == 1
        assert "test.event" in bus.subscribers
        assert bus.subscribers["test.event"] == [(subscriber.handler, 0)]

    def test_event_bus_subscribe_with_priority(self):
        """Test event subscription with priority."""
        bus = EventBus()

        # Create mock subscribers
        subscriber1 = Mock()
        subscriber2 = Mock()

        # Subscribe with different priorities
        bus.subscribe("test.event", subscriber1.handler, priority=10)
        bus.subscribe("test.event", subscriber2.handler, priority=5)

        # Check subscription order (higher priority first)
        assert len(bus.subscribers) == 1
        assert "test.event" in bus.subscribers
        subscribers = bus.subscribers["test.event"]
        assert len(subscribers) == 2
        assert subscribers[0] == (subscriber1.handler, 10)
        assert subscribers[1] == (subscriber2.handler, 5)

    def test_event_bus_publish(self):
        """Test event publishing."""
        bus = EventBus()

        # Create mock subscriber
        subscriber = Mock()
        bus.subscribe("test.event", subscriber.handler)

        # Publish event
        event_data = {"key": "value"}
        bus.publish("test.event", event_data)

        # Check subscriber was called
        subscriber.handler.assert_called_once_with("test.event", event_data)

    def test_event_bus_publish_multiple_subscribers(self):
        """Test event publishing to multiple subscribers."""
        bus = EventBus()

        # Create mock subscribers
        subscriber1 = Mock()
        subscriber2 = Mock()

        bus.subscribe("test.event", subscriber1.handler)
        bus.subscribe("test.event", subscriber2.handler)

        # Publish event
        event_data = {"key": "value"}
        bus.publish("test.event", event_data)

        # Check both subscribers were called
        subscriber1.handler.assert_called_once_with("test.event", event_data)
        subscriber2.handler.assert_called_once_with("test.event", event_data)

    def test_event_bus_publish_wildcard(self):
        """Test event publishing with wildcard subscription."""
        bus = EventBus()

        # Create mock subscriber
        subscriber = Mock()
        bus.subscribe("*", subscriber.handler)

        # Publish event
        event_data = {"key": "value"}
        bus.publish("test.event", event_data)

        # Check subscriber was called
        subscriber.handler.assert_called_once_with("test.event", event_data)

    def test_event_bus_publish_pattern_matching(self):
        """Test event publishing with pattern matching."""
        bus = EventBus()

        # Create mock subscribers
        subscriber1 = Mock()
        subscriber2 = Mock()

        bus.subscribe("test.*", subscriber1.handler)
        bus.subscribe("other.*", subscriber2.handler)

        # Publish event
        event_data = {"key": "value"}
        bus.publish("test.event", event_data)

        # Check only matching subscriber was called
        subscriber1.handler.assert_called_once_with("test.event", event_data)
        subscriber2.handler.assert_not_called()

    def test_event_bus_unsubscribe(self):
        """Test event unsubscription."""
        bus = EventBus()

        # Create mock subscriber
        subscriber = Mock()
        bus.subscribe("test.event", subscriber.handler)

        # Check subscription
        assert len(bus.subscribers) == 1

        # Unsubscribe
        bus.unsubscribe("test.event", subscriber.handler)

        # Check unsubscription
        assert len(bus.subscribers) == 0

    def test_event_bus_clear(self):
        """Test event bus clearing."""
        bus = EventBus()

        # Create mock subscriber
        subscriber = Mock()
        bus.subscribe("test.event", subscriber.handler)

        # Check subscription
        assert len(bus.subscribers) == 1

        # Clear
        bus.clear()

        # Check clearing
        assert len(bus.subscribers) == 0

    def test_event_bus_get_events(self):
        """Test event bus event retrieval."""
        bus = EventBus()

        # Publish events
        bus.publish("test.event1", {"data": "1"})
        bus.publish("test.event2", {"data": "2"})

        # Get events
        events = bus.get_events()

        # Check events
        assert len(events) == 2
        assert events[0]["event"] == "test.event1"
        assert events[0]["data"] == {"data": "1"}
        assert events[1]["event"] == "test.event2"
        assert events[1]["data"] == {"data": "2"}

    def test_event_bus_get_events_by_type(self):
        """Test event bus event retrieval by type."""
        bus = EventBus()

        # Publish events
        bus.publish("test.event1", {"data": "1"})
        bus.publish("test.event2", {"data": "2"})
        bus.publish("other.event", {"data": "3"})

        # Get events by type
        test_events = bus.get_events_by_type("test.*")
        other_events = bus.get_events_by_type("other.*")

        # Check events
        assert len(test_events) == 2
        assert len(other_events) == 1
        assert test_events[0]["event"] == "test.event1"
        assert test_events[1]["event"] == "test.event2"
        assert other_events[0]["event"] == "other.event"


class TestLoggingSubscriber:
    """Test LoggingSubscriber functionality."""

    def test_logging_subscriber_creation(self):
        """Test LoggingSubscriber creation."""
        logger = Mock()
        subscriber = LoggingSubscriber(logger)

        # Check subscriber properties
        assert subscriber.logger == logger

    def test_logging_subscriber_handler(self):
        """Test LoggingSubscriber handler."""
        logger = Mock()
        subscriber = LoggingSubscriber(logger)

        # Call handler
        event = "test.event"
        data = {"key": "value"}
        subscriber.handler(event, data)

        # Check logger was called
        logger.info.assert_called_once()
        call_args = logger.info.call_args[0][0]
        assert "test.event" in call_args
        assert "key" in call_args

    def test_logging_subscriber_handler_with_json(self):
        """Test LoggingSubscriber handler with JSON data."""
        logger = Mock()
        subscriber = LoggingSubscriber(logger)

        # Call handler with JSON data
        event = "test.event"
        data = {"key": "value", "nested": {"data": "test"}}
        subscriber.handler(event, data)

        # Check logger was called
        logger.info.assert_called_once()
        call_args = logger.info.call_args[0][0]
        assert "test.event" in call_args
        assert "key" in call_args
        assert "nested" in call_args

    def test_logging_subscriber_handler_with_exception(self):
        """Test LoggingSubscriber handler with exception."""
        logger = Mock()
        subscriber = LoggingSubscriber(logger)

        # Call handler with exception data
        event = "test.event"
        data = {"exception": "Test exception", "traceback": "Test traceback"}
        subscriber.handler(event, data)

        # Check logger was called
        logger.error.assert_called_once()
        call_args = logger.error.call_args[0][0]
        assert "test.event" in call_args
        assert "Test exception" in call_args


class TestLogging:
    """Test logging functionality."""

    def test_init_logging_default(self):
        """Test logging initialization with default settings."""
        # Initialize logging
        init_logging()

        # Get logger
        logger = get_logger("test")

        # Check logger
        assert logger.name == "test"
        assert logger.level == 20  # INFO level

    def test_init_logging_json_mode(self):
        """Test logging initialization with JSON mode."""
        # Initialize logging with JSON mode
        init_logging(json_mode=True)

        # Get logger
        logger = get_logger("test")

        # Check logger
        assert logger.name == "test"
        assert logger.level == 20  # INFO level

    def test_init_logging_debug_level(self):
        """Test logging initialization with debug level."""
        # Initialize logging with debug level
        init_logging(level="DEBUG")

        # Get logger
        logger = get_logger("test")

        # Check logger
        assert logger.name == "test"
        assert logger.level == 10  # DEBUG level

    def test_get_logger(self):
        """Test logger retrieval."""
        # Initialize logging
        init_logging()

        # Get logger
        logger = get_logger("test")

        # Check logger
        assert logger.name == "test"
        assert logger.level == 20  # INFO level

    def test_get_logger_different_names(self):
        """Test logger retrieval with different names."""
        # Initialize logging
        init_logging()

        # Get loggers with different names
        logger1 = get_logger("test1")
        logger2 = get_logger("test2")

        # Check loggers
        assert logger1.name == "test1"
        assert logger2.name == "test2"
        assert logger1 != logger2

    def test_get_logger_same_name(self):
        """Test logger retrieval with same name."""
        # Initialize logging
        init_logging()

        # Get logger with same name
        logger1 = get_logger("test")
        logger2 = get_logger("test")

        # Check loggers are the same
        assert logger1 == logger2


class TestEventLoggingIntegration:
    """Test event and logging integration."""

    def test_event_bus_with_logging_subscriber(self):
        """Test EventBus with LoggingSubscriber."""
        # Initialize logging
        init_logging()

        # Get logger
        logger = get_logger("test")

        # Create event bus
        bus = EventBus()

        # Create logging subscriber
        subscriber = LoggingSubscriber(logger)
        bus.subscribe("test.event", subscriber.handler)

        # Publish event
        event_data = {"key": "value"}
        bus.publish("test.event", event_data)

        # Check logger was called
        logger.info.assert_called_once()

    def test_event_bus_with_multiple_logging_subscribers(self):
        """Test EventBus with multiple LoggingSubscribers."""
        # Initialize logging
        init_logging()

        # Get loggers
        logger1 = get_logger("test1")
        logger2 = get_logger("test2")

        # Create event bus
        bus = EventBus()

        # Create logging subscribers
        subscriber1 = LoggingSubscriber(logger1)
        subscriber2 = LoggingSubscriber(logger2)

        bus.subscribe("test.event", subscriber1.handler)
        bus.subscribe("test.event", subscriber2.handler)

        # Publish event
        event_data = {"key": "value"}
        bus.publish("test.event", event_data)

        # Check both loggers were called
        logger1.info.assert_called_once()
        logger2.info.assert_called_once()

    def test_event_bus_with_wildcard_logging_subscriber(self):
        """Test EventBus with wildcard LoggingSubscriber."""
        # Initialize logging
        init_logging()

        # Get logger
        logger = get_logger("test")

        # Create event bus
        bus = EventBus()

        # Create logging subscriber with wildcard
        subscriber = LoggingSubscriber(logger)
        bus.subscribe("*", subscriber.handler)

        # Publish events
        bus.publish("test.event1", {"data": "1"})
        bus.publish("test.event2", {"data": "2"})

        # Check logger was called for both events
        assert logger.info.call_count == 2

    def test_event_bus_with_pattern_logging_subscriber(self):
        """Test EventBus with pattern LoggingSubscriber."""
        # Initialize logging
        init_logging()

        # Get logger
        logger = get_logger("test")

        # Create event bus
        bus = EventBus()

        # Create logging subscriber with pattern
        subscriber = LoggingSubscriber(logger)
        bus.subscribe("test.*", subscriber.handler)

        # Publish events
        bus.publish("test.event1", {"data": "1"})
        bus.publish("other.event", {"data": "2"})

        # Check logger was called only for matching event
        assert logger.info.call_count == 1

    def test_event_bus_with_json_logging_subscriber(self):
        """Test EventBus with JSON LoggingSubscriber."""
        # Initialize logging with JSON mode
        init_logging(json_mode=True)

        # Get logger
        logger = get_logger("test")

        # Create event bus
        bus = EventBus()

        # Create logging subscriber
        subscriber = LoggingSubscriber(logger)
        bus.subscribe("test.event", subscriber.handler)

        # Publish event
        event_data = {"key": "value", "nested": {"data": "test"}}
        bus.publish("test.event", event_data)

        # Check logger was called
        logger.info.assert_called_once()
        call_args = logger.info.call_args[0][0]
        assert "test.event" in call_args
        assert "key" in call_args
        assert "nested" in call_args

    def test_event_bus_with_exception_logging_subscriber(self):
        """Test EventBus with exception LoggingSubscriber."""
        # Initialize logging
        init_logging()

        # Get logger
        logger = get_logger("test")

        # Create event bus
        bus = EventBus()

        # Create logging subscriber
        subscriber = LoggingSubscriber(logger)
        bus.subscribe("test.event", subscriber.handler)

        # Publish event with exception
        event_data = {"exception": "Test exception", "traceback": "Test traceback"}
        bus.publish("test.event", event_data)

        # Check logger was called with error level
        logger.error.assert_called_once()
        call_args = logger.error.call_args[0][0]
        assert "test.event" in call_args
        assert "Test exception" in call_args


class TestEventLoggingRealWorld:
    """Test event and logging in real-world scenarios."""

    def test_pipeline_execution_events(self):
        """Test pipeline execution events."""
        # Initialize logging
        init_logging()

        # Get logger
        logger = get_logger("pipeline")

        # Create event bus
        bus = EventBus()

        # Create logging subscriber
        subscriber = LoggingSubscriber(logger)
        bus.subscribe("pipeline.*", subscriber.handler)

        # Simulate pipeline execution
        bus.publish("pipeline.started", {"pipeline_name": "test_pipeline"})
        bus.publish("pipeline.step.started", {"step_name": "CollectSeeds"})
        bus.publish("pipeline.step.succeeded", {"step_name": "CollectSeeds", "duration_s": 1.5})
        bus.publish("pipeline.step.started", {"step_name": "ComputeMerkle"})
        bus.publish("pipeline.step.succeeded", {"step_name": "ComputeMerkle", "duration_s": 0.5})
        bus.publish("pipeline.succeeded", {"pipeline_name": "test_pipeline", "duration_s": 2.0})

        # Check logger was called for all events
        assert logger.info.call_count == 6

    def test_pack_build_events(self):
        """Test pack build events."""
        # Initialize logging
        init_logging()

        # Get logger
        logger = get_logger("pack")

        # Create event bus
        bus = EventBus()

        # Create logging subscriber
        subscriber = LoggingSubscriber(logger)
        bus.subscribe("pack.*", subscriber.handler)

        # Simulate pack build
        bus.publish("pack.building", {"pack_name": "test-pack", "version": "v0.1.0"})
        bus.publish(
            "pack.built",
            {
                "pack_name": "test-pack",
                "version": "v0.1.0",
                "zip_path": "/path/to/pack.zip",
            },
        )

        # Check logger was called for all events
        assert logger.info.call_count == 2

    def test_metrics_events(self):
        """Test metrics events."""
        # Initialize logging
        init_logging()

        # Get logger
        logger = get_logger("metrics")

        # Create event bus
        bus = EventBus()

        # Create logging subscriber
        subscriber = LoggingSubscriber(logger)
        bus.subscribe("metrics.*", subscriber.handler)

        # Simulate metrics processing
        bus.publish(
            "metrics.summary.built",
            {"summary_path": "/path/to/summary.json", "file_count": 5},
        )
        bus.publish(
            "metrics.aggregated",
            {"metric_name": "coverage_gain", "value": 0.75, "weighted_avg": 0.8},
        )

        # Check logger was called for all events
        assert logger.info.call_count == 2

    def test_signing_events(self):
        """Test signing events."""
        # Initialize logging
        init_logging()

        # Get logger
        logger = get_logger("signing")

        # Create event bus
        bus = EventBus()

        # Create logging subscriber
        subscriber = LoggingSubscriber(logger)
        bus.subscribe("sign.*", subscriber.handler)

        # Simulate signing
        bus.publish(
            "sign.started",
            {"artifact_path": "/path/to/artifact.zip", "provider": "cosign"},
        )
        bus.publish(
            "sign.succeeded",
            {
                "artifact_path": "/path/to/artifact.zip",
                "signature_path": "/path/to/artifact.zip.sig",
            },
        )

        # Check logger was called for all events
        assert logger.info.call_count == 2

    def test_verification_events(self):
        """Test verification events."""
        # Initialize logging
        init_logging()

        # Get logger
        logger = get_logger("verification")

        # Create event bus
        bus = EventBus()

        # Create logging subscriber
        subscriber = LoggingSubscriber(logger)
        bus.subscribe("pack.verify.*", subscriber.handler)

        # Simulate verification
        bus.publish("pack.verify.started", {"zip_path": "/path/to/pack.zip"})
        bus.publish(
            "pack.verify.succeeded",
            {
                "zip_path": "/path/to/pack.zip",
                "checks": {
                    "manifest_valid": True,
                    "files_sha256": True,
                    "merkle_root": True,
                },
            },
        )

        # Check logger was called for all events
        assert logger.info.call_count == 2
