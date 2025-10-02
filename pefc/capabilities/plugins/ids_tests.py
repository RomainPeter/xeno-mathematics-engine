from __future__ import annotations

from typing import Any, Dict, List

from pefc.capabilities.core import CapMeta
from pefc.pcap.model import ProofSpec


class IDSTestSynthesizer:
    """IDS test synthesizer capability."""

    def __init__(self, n_seeds: int = 24):
        self._meta = CapMeta(
            id="cap-ids-tests",
            provides=["tests.synthetic"],
            prerequisites=[],
            cost_hint_V={"time": 0.3},
        )
        self.n_seeds = n_seeds

    @property
    def meta(self):
        return self._meta

    def can_handle(self, incident: Dict[str, Any]) -> bool:
        return incident.get("type") in ("robustness.fuzz", "regression.suspect")

    def plan(self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None) -> List[ProofSpec]:
        target = (incident.get("context") or {}).get("target", "unknown")
        return [
            ProofSpec(
                type="ids.generate",
                args={
                    "target": target,
                    "n_seeds": self.n_seeds,
                    "criteria": ["boundary", "mutation", "adversarial"],
                },
                expect={"fail_rate_max": 0.0},
            )
        ]
