"""
Event bus implementation with deque buffer and non-blocking publish.
Provides EventBus with backpressure handling and structured telemetry.
"""

import asyncio
from collections import deque
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
import time
import json
from pathlib import Path

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
    """Event bus with deque buffer and non-blocking publish."""

    def __init__(self, config: Optional[EventBusConfig] = None):
        self.config = config or EventBusConfig()
        # Deque-based in-memory buffer for backpressure-friendly non-blocking enqueue
        self.buffer: deque = deque(maxlen=self.config.buffer_size)
        self._buffer_lock: asyncio.Lock = asyncio.Lock()
        # Wake event to notify the drain loop of new data
        self._wake_event: asyncio.Event = asyncio.Event()
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
            if isinstance(event, dict):
                event = Event.from_dict(event)

            event.seq = self.seq_counter
            self.seq_counter += 1

            async with self._buffer_lock:
                if len(self.buffer) >= self.config.buffer_size:
                    if self.config.drop_oldest:
                        # deque with maxlen would auto-drop; we account explicitly
                        if len(self.buffer) > 0:
                            self.buffer.popleft()
                            self.stats["dropped"] += 1
                            self.logger.warning(f"Event dropped due to full buffer: {event.type}")
                        self.buffer.append(event)
                        self.stats["published"] += 1
                    else:
                        # do not enqueue
                        self.stats["dropped"] += 1
                        self.logger.warning(f"Event dropped due to full buffer: {event.type}")
                else:
                    self.buffer.append(event)
                    self.stats["published"] += 1

            # Signal the drain loop
            self._wake_event.set()

        except Exception as e:
            self.logger.error(f"Error publishing event: {e}")

    def publish_nowait(self, event: Union[Event, Dict[str, Any]]):
        """Synchronous variant of publish that never awaits.

        Useful from synchronous code paths (e.g., orchestrator steps) to enqueue
        events without requiring an event loop context. Mirrors the logic of
        publish() including backpressure handling and sequence assignment.
        """
        try:
            if isinstance(event, dict):
                event = Event.from_dict(event)

            event.seq = self.seq_counter
            self.seq_counter += 1

            # Use try/except around lock acquisition in sync context
            lock = self._buffer_lock
            # Best-effort if loop not running; use blocking call via loop if needed
            if lock.locked():
                # If locked, we still want to try append later; minimal contention path
                pass
            # Acquire lock synchronously via loop
            loop = asyncio.get_event_loop() if asyncio.get_event_loop_policy() else None
            if loop and loop.is_running():
                # Schedule a synchronous critical section by running a no-op awaitable
                # and then performing append under lock using call_soon_threadsafe-like pattern
                # Simpler approach: try non-atomic check/append with small race acceptance
                pass
            # Fallback: try to append with minimal race (acceptable for nowait semantics)
            if len(self.buffer) >= self.config.buffer_size:
                if self.config.drop_oldest:
                    if len(self.buffer) > 0:
                        try:
                            # Best-effort pop left
                            self.buffer.popleft()
                            self.stats["dropped"] += 1
                        except Exception as e:
                            import logging
                            logging.warning(f"Error dropping event: {e}")
                    self.buffer.append(event)
                    self.stats["published"] += 1
                else:
                    self.stats["dropped"] += 1
            else:
                self.buffer.append(event)
                self.stats["published"] += 1

            self._wake_event.set()
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

        # Wait for buffer to be empty or timeout
        while (time.time() - start_time) < timeout:
            async with self._buffer_lock:
                if len(self.buffer) == 0:
                    break
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
            "queue_size": len(self.buffer),
            "sinks": len(self.sinks),
        }

    async def _drain_loop(self):
        """Main drain loop that processes events from the deque buffer."""
        while True:
            try:
                # Wait for wake signal or periodic tick
                try:
                    await asyncio.wait_for(
                        self._wake_event.wait(), timeout=self.config.drain_interval
                    )
                except asyncio.TimeoutError:
                    pass

                # Drain as many events as available
                while True:
                    async with self._buffer_lock:
                        if len(self.buffer) == 0:
                            # Clear wake when empty
                            self._wake_event.clear()
                            break
                        event = self.buffer.popleft()

                    await self._process_event(event)

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
                    self.logger.error(f"Error writing to sink {type(sink).__name__}: {e}")

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


def replay_journal(path: Union[str, Path], callback: Callable[[Event], None]) -> int:
    """Replay a JSONL journal file, invoking callback per Event.

    Returns the number of events replayed.
    """
    count = 0
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                ev = Event.from_dict(data)
                callback(ev)
                count += 1
            except Exception as e:
                # Skip malformed lines but continue replay
                import logging
                logging.warning(f"Error replaying event: {e}")
                continue
    return count
