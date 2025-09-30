from __future__ import annotations
from typing import Dict, Any, List
from pefc.capabilities.base import CapabilityMetadata
from pefc.incidents.types import CapabilityResult
from pefc.capabilities.loader import build_capabilities
from pefc.capabilities.manager import CapabilityManager


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

    def score(self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None) -> float:
        return 0.6

    def check_prerequisites(self) -> List[str]:
        return []

    def handle(self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None) -> Dict[str, Any]:
        # Use capabilities to generate PCAP
        caps_cfg = (ctx or {}).get("capabilities_cfg") or {}
        caps = build_capabilities(caps_cfg)
        manager = CapabilityManager(caps)
        pcap = manager.plan_pcap(
            action="incident.remediation.plan",
            incident=incident,
            obligations=incident.get("obligations", []),
            ctx=ctx,
        )
        return CapabilityResult(
            handler_id=self.meta.id,
            status="planned",
            proofs=[],  # Now in PCAP
            messages=["composed by capabilities"],
            meta={"caps": pcap.meta, "pcap": pcap.model_dump()},
        ).__dict__
