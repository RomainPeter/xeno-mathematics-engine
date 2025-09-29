"""
Deterministic Verifier stub for lab mode.
"""

from typing import Dict, Any, List, Optional


class VerifierStub:
    def __init__(self, scenarios: Optional[List[Dict[str, Any]]] = None):
        """scenarios: list of dicts like {"valid": bool, "confidence": float} or {"valid": False, "failing_property": str}
        Emitted sequentially per verify call.
        """
        self._scenarios = scenarios or [
            {"valid": True, "confidence": 0.9, "evidence": {}, "metrics": {}}
        ]
        self._idx = 0

    async def verify(
        self,
        specification: Dict[str, Any],
        implementation: Dict[str, Any],
        constraints: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if self._idx < len(self._scenarios):
            out = self._scenarios[self._idx]
            self._idx += 1
            return out
        return {"valid": True, "confidence": 0.9, "evidence": {}, "metrics": {}}
