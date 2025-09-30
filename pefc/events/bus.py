from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Tuple
import time
import threading
import fnmatch

EventHandler = Callable[["Event"], None]


@dataclass(frozen=True)
class Event:
    """Event with topic, timestamp, and data."""

    topic: str
    ts: float
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class _Subscription:
    """Internal subscription representation."""

    pattern: str
    handler: EventHandler
    once: bool
    priority: int


class EventBus:
    """Thread-safe event bus with wildcard support and priorities."""

    def __init__(self) -> None:
        self._subs: List[_Subscription] = []
        self._lock = threading.RLock()

    def subscribe(
        self,
        pattern: str,
        handler: EventHandler,
        *,
        once: bool = False,
        priority: int = 0,
    ) -> None:
        """Subscribe to events matching pattern."""
        with self._lock:
            self._subs.append(_Subscription(pattern, handler, once, priority))
            # Sort by priority descending for execution order
            self._subs.sort(key=lambda s: s.priority, reverse=True)

    def unsubscribe(self, handler: EventHandler) -> None:
        """Unsubscribe handler from all patterns."""
        with self._lock:
            self._subs = [s for s in self._subs if s.handler is not handler]

    def clear(self) -> None:
        """Clear all subscriptions."""
        with self._lock:
            self._subs.clear()

    def emit(self, topic: str, **data: Any) -> None:
        """Emit event to all matching subscribers."""
        ev = Event(topic=topic, ts=time.time(), data=data)
        to_call: List[Tuple[int, _Subscription]] = []
        removals: List[_Subscription] = []

        with self._lock:
            for idx, s in enumerate(self._subs):
                if fnmatch.fnmatchcase(topic, s.pattern):
                    to_call.append((idx, s))

        # Call handlers outside lock to avoid deadlocks
        for idx, s in to_call:
            try:
                s.handler(ev)
            except Exception:
                # Bus should never crash; let logger subscriber capture errors
                pass
            if s.once:
                removals.append(s)

        # Remove once subscriptions
        if removals:
            with self._lock:
                self._subs = [s for s in self._subs if s not in removals]
