from __future__ import annotations
from typing import Dict, Any, List
from pefc.capabilities.base import CapabilityMetadata
from pefc.incidents.types import CapabilityResult
from pefc.capabilities.loader import build_capabilities
from pefc.capabilities.manager import CapabilityManager


class HSTreeHandler:
    """Handler for HS-Tree capability."""

    def __init__(self, **params):
        self.params = params
        self._meta = CapabilityMetadata(
            id="hs-tree",
            provides=["security.policy.violation", "traceability.gap"],
            prerequisites=[],  # ex: ["bin:hstree"]
            cost_hint_V={"audit_cost": 0.3, "time": 0.2},
        )

    @property
    def meta(self) -> CapabilityMetadata:
        return self._meta

    def can_handle(self, incident_type: str) -> bool:
        return incident_type in self._meta.provides

    def score(
        self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None
    ) -> float:
        sev = {
            "info": 0.1,
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "critical": 1.0,
        }.get(incident.get("severity", "low"), 0.4)
        return 0.6 + 0.4 * sev  # favor incidents "policy/traceability"

    def check_prerequisites(self) -> List[str]:
        return []  # stub: all available

    def handle(
        self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
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
