from __future__ import annotations

import logging
from typing import List

from .bus import Event


class MemorySink:
    """Memory sink for testing and debugging."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handler(self, ev: Event) -> None:
        """Store event in memory."""
        self.events.append(ev)


class LoggingSubscriber:
    """Logging subscriber for structured event logging."""

    def __init__(self, logger: logging.Logger) -> None:
        self.log = logger

    def handler(self, ev: Event) -> None:
        """Log event with appropriate level."""
        # Error level for failed/error events, info otherwise
        lvl = (
            logging.ERROR
            if ev.topic.endswith(("failed", "error")) or ".fail" in ev.topic
            else logging.INFO
        )
        self.log.log(lvl, "event", extra={"event": ev.topic, **ev.data})


class PrometheusStub:
    """Prometheus metrics stub for event counting."""

    def __init__(self) -> None:
        self.counts = {}

    def handler(self, ev: Event) -> None:
        """Count events by topic."""
        self.counts[ev.topic] = self.counts.get(ev.topic, 0) + 1
