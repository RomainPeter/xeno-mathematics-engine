"""
Deterministic LLM stub for lab mode.
"""

import asyncio
import random
from typing import Any, Dict, List, Optional


class LLMStub:
    def __init__(
        self,
        seed: Optional[int] = None,
        script: Optional[List[Dict[str, Any]]] = None,
        delay_ms: int = 0,
    ):
        self._rng = random.Random(seed)
        self._script = script or []
        self._idx = 0
        self._delay_ms = delay_ms

    async def generate(
        self, prompt: str, max_tokens: int = 256, temperature: float = 0.0
    ) -> Dict[str, Any]:
        if self._delay_ms > 0:
            await asyncio.sleep(self._delay_ms / 1000.0)
        if self._idx < len(self._script):
            out = self._script[self._idx]
            self._idx += 1
            return out
        # Fallback deterministic structure
        return {
            "name": f"spec_{self._rng.randint(0, 9999)}",
            "constraints": [],
            "properties": [],
        }
