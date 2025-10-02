"""
Bus d'événements asynchrone pour l'orchestrator.
"""

import asyncio
from typing import Any


class EventBus:
    """Bus d'événements asynchrone."""

    def __init__(self) -> None:
        self.q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def emit(self, event: dict[str, Any]) -> None:
        """Émet un événement."""
        await self.q.put(event)

    async def drain(self):
        """Draine tous les événements en attente."""
        while not self.q.empty():
            yield await self.q.get()
