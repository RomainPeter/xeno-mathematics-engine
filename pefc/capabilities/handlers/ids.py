from __future__ import annotations
from typing import Dict, Any, List
from pefc.capabilities.base import CapabilityMetadata
from pefc.incidents.types import CapabilityResult


class IDSHandler:
    """Handler for IDS synthesis capability."""

    def __init__(self, n_seeds: int = 16, **kw):
        self.n_seeds = n_seeds
        self._meta = CapabilityMetadata(
            id="ids-synth",
            provides=["robustness.fuzz", "regression.suspect"],
            prerequisites=[],
            cost_hint_V={"time": 0.3},
        )

    @property
    def meta(self):
        return self._meta

    def can_handle(self, incident_type: str) -> bool:
        return incident_type in self._meta.provides

    def score(
        self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None
    ) -> float:
        return 0.6

    def check_prerequisites(self) -> List[str]:
        return []

    def handle(
        self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        proofs = [
            {
                "type": "ids-generate-tests",
                "n_seeds": self.n_seeds,
                "target": incident.get("context", {}).get("target", "unknown"),
                "criteria": ["boundary", "mutation", "adversarial"],
            }
        ]
        return CapabilityResult(
            handler_id=self.meta.id,
            status="planned",
            proofs=proofs,
            messages=["ids plan"],
            meta={"n_seeds": self.n_seeds},
        ).__dict__
