"""
Event bus implementation with asyncio.Queue and non-blocking publish.
Provides EventBus with backpressure handling and structured telemetry.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
import time

from .types import Event
from .sinks import EventSink, StdoutJSONLSink, FileJSONLSink, MemorySink


@dataclass
class EventBusConfig:
    """Configuration for EventBus."""

    buffer_size: int = 4096
    sinks: List[str] = field(default_factory=lambda: ["stdout"])
    file_path: Optional[str] = None
    drop_oldest: bool = True
    flush_timeout: float = 5.0
    drain_interval: float = 0.1


class EventBus:
    """Event bus with asyncio.Queue and non-blocking publish."""

    def __init__(self, config: Optional[EventBusConfig] = None):
        self.config = config or EventBusConfig()
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.buffer_size)
        self.sinks: List[EventSink] = []
        self.subscribers: List[Callable] = []
        self.drain_task: Optional[asyncio.Task] = None
        self.seq_counter = 0
        self.stats = {
            "published": 0,
            "dropped": 0,
            "written": 0,
            "subscribers": 0,
        }
        self.logger = logging.getLogger(__name__)

        # Initialize sinks
        self._initialize_sinks()

    def _initialize_sinks(self):
        """Initialize configured sinks."""
        for sink_name in self.config.sinks:
            if sink_name == "stdout":
                self.sinks.append(StdoutJSONLSink())
            elif sink_name == "file" and self.config.file_path:
                self.sinks.append(FileJSONLSink(self.config.file_path))
            elif sink_name == "memory":
                self.sinks.append(MemorySink())
            else:
                self.logger.warning(f"Unknown sink: {sink_name}")

    async def start(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """Start the event bus drain task."""
        if self.drain_task and not self.drain_task.done():
            return

        self.drain_task = asyncio.create_task(self._drain_loop())
        self.logger.info("EventBus started")

    async def stop(self):
        """Stop the event bus and flush remaining events."""
        if self.drain_task:
            self.drain_task.cancel()
            try:
                await self.drain_task
            except asyncio.CancelledError:
                pass

        # Flush remaining events
        await self.flush(self.config.flush_timeout)
        self.logger.info("EventBus stopped")

    async def publish(self, event: Union[Event, Dict[str, Any]]):
        """Publish an event non-blocking."""
        try:
            # Convert to Event if needed
            if isinstance(event, dict):
                event = Event.from_dict(event)

            # Set sequence number
            event.seq = self.seq_counter
            self.seq_counter += 1

            # Try to put in queue
            try:
                self.queue.put_nowait(event)
                self.stats["published"] += 1
            except asyncio.QueueFull:
                # Handle backpressure
                if self.config.drop_oldest:
                    # Remove oldest event
                    try:
                        self.queue.get_nowait()
                        self.queue.put_nowait(event)
                        self.stats["dropped"] += 1
                        self.stats["published"] += 1
                        self.logger.warning(
                            f"Event dropped due to full buffer: {event.type}"
                        )
                    except asyncio.QueueEmpty:
                        # Queue became empty, try again
                        self.queue.put_nowait(event)
                        self.stats["published"] += 1
                else:
                    # Drop new event
                    self.stats["dropped"] += 1
                    self.logger.warning(
                        f"Event dropped due to full buffer: {event.type}"
                    )

        except Exception as e:
            self.logger.error(f"Error publishing event: {e}")

    def publish_nowait(self, event: Union[Event, Dict[str, Any]]):
        """Synchronous variant of publish that never awaits.

        Useful from synchronous code paths (e.g., orchestrator steps) to enqueue
        events without requiring an event loop context. Mirrors the logic of
        publish() including backpressure handling and sequence assignment.
        """
        try:
            # Convert to Event if needed
            if isinstance(event, dict):
                event = Event.from_dict(event)

            # Set sequence number
            event.seq = self.seq_counter
            self.seq_counter += 1

            # Try to put in queue
            try:
                self.queue.put_nowait(event)
                self.stats["published"] += 1
            except asyncio.QueueFull:
                # Handle backpressure
                if self.config.drop_oldest:
                    # Remove oldest event
                    try:
                        self.queue.get_nowait()
                        self.queue.put_nowait(event)
                        self.stats["dropped"] += 1
                        self.stats["published"] += 1
                        self.logger.warning(
                            f"Event dropped due to full buffer: {event.type}"
                        )
                    except asyncio.QueueEmpty:
                        # Queue became empty, try again
                        self.queue.put_nowait(event)
                        self.stats["published"] += 1
                else:
                    # Drop new event
                    self.stats["dropped"] += 1
                    self.logger.warning(
                        f"Event dropped due to full buffer: {event.type}"
                    )

        except Exception as e:
            self.logger.error(f"Error publishing event (nowait): {e}")

    def subscribe(self, callback: Callable[[Event], None]):
        """Subscribe to events with a callback."""
        self.subscribers.append(callback)
        self.stats["subscribers"] = len(self.subscribers)
        self.logger.info(f"Subscriber added, total: {len(self.subscribers)}")

    async def flush(self, timeout: float = 5.0):
        """Flush all pending events."""
        start_time = time.time()

        # Wait for queue to be empty or timeout
        while not self.queue.empty() and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.01)

        # Flush all sinks
        for sink in self.sinks:
            if hasattr(sink, "flush"):
                sink.flush()

        self.logger.info(f"EventBus flushed in {time.time() - start_time:.3f}s")

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            **self.stats,
            "queue_size": self.queue.qsize(),
            "sinks": len(self.sinks),
        }

    async def _drain_loop(self):
        """Main drain loop that processes events from queue."""
        while True:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(
                    self.queue.get(), timeout=self.config.drain_interval
                )

                # Process event
                await self._process_event(event)

            except asyncio.TimeoutError:
                # No events in queue, continue
                continue
            except Exception as e:
                self.logger.error(f"Error in drain loop: {e}")
                await asyncio.sleep(0.1)

    async def _process_event(self, event: Event):
        """Process a single event."""
        try:
            # Convert to JSON
            event_dict = event.to_dict()

            # Write to all sinks
            for sink in self.sinks:
                try:
                    sink.write(event_dict)
                    self.stats["written"] += 1
                except Exception as e:
                    self.logger.error(
                        f"Error writing to sink {type(sink).__name__}: {e}"
                    )

            # Notify subscribers
            for callback in self.subscribers:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    self.logger.error(f"Error in subscriber callback: {e}")

        except Exception as e:
            self.logger.error(f"Error processing event: {e}")

    def add_sink(self, sink: EventSink):
        """Add a new sink to the event bus."""
        self.sinks.append(sink)
        self.logger.info(f"Sink added: {type(sink).__name__}")

    def remove_sink(self, sink: EventSink):
        """Remove a sink from the event bus."""
        if sink in self.sinks:
            self.sinks.remove(sink)
            self.logger.info(f"Sink removed: {type(sink).__name__}")

    def clear_subscribers(self):
        """Clear all subscribers."""
        self.subscribers.clear()
        self.stats["subscribers"] = 0
        self.logger.info("All subscribers cleared")

    def reset_stats(self):
        """Reset event bus statistics."""
        self.stats = {
            "published": 0,
            "dropped": 0,
            "written": 0,
            "subscribers": len(self.subscribers),
        }
        self.seq_counter = 0
        self.logger.info("Event bus statistics reset")


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_global_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def set_global_event_bus(event_bus: EventBus):
    """Set the global event bus instance."""
    global _global_event_bus
    _global_event_bus = event_bus


async def publish_event(event: Union[Event, Dict[str, Any]]):
    """Publish an event to the global event bus."""
    bus = get_global_event_bus()
    await bus.publish(event)


def publish_event_nowait(event: Union[Event, Dict[str, Any]]):
    """Synchronous helper to publish to the global event bus without awaiting."""
    bus = get_global_event_bus()
    bus.publish_nowait(event)


async def start_global_event_bus(config: Optional[EventBusConfig] = None):
    """Start the global event bus."""
    bus = get_global_event_bus()
    if config:
        bus.config = config
    await bus.start()


async def stop_global_event_bus():
    """Stop the global event bus."""
    bus = get_global_event_bus()
    await bus.stop()
