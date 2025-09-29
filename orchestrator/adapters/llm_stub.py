"""
Deterministic LLM stub for lab mode.
"""

from typing import Dict, Any, List, Optional
import random


class LLMStub:
    def __init__(
        self, seed: Optional[int] = None, script: Optional[List[Dict[str, Any]]] = None
    ):
        self._rng = random.Random(seed)
        self._script = script or []
        self._idx = 0

    async def generate(
        self, prompt: str, max_tokens: int = 256, temperature: float = 0.0
    ) -> Dict[str, Any]:
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
