# Events package for EventBus
from __future__ import annotations
from typing import Optional
from .bus import EventBus

_BUS: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get singleton event bus instance."""
    global _BUS
    if _BUS is None:
        _BUS = EventBus()
    return _BUS
