from __future__ import annotations

from typing import Any, Dict, List

from pefc.capabilities.base import CapabilityMetadata, have_tool
from pefc.capabilities.loader import build_capabilities
from pefc.capabilities.manager import CapabilityManager
from pefc.incidents.types import CapabilityResult


class OPAHandler:
    """Handler for OPA Rego capability."""

    def __init__(self, policy_dir: str = "policies", query: str = "data.pefc.allow", **kw):
        self.policy_dir = policy_dir
        self.query = query
        self._meta = CapabilityMetadata(
            id="opa-rego",
            provides=["security.policy.violation", "compliance.check"],
            prerequisites=["bin:opa"],
            cost_hint_V={"audit_cost": 0.2, "time": 0.1},
        )

    @property
    def meta(self):
        return self._meta

    def can_handle(self, incident_type: str) -> bool:
        return incident_type in self._meta.provides

    def score(self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None) -> float:
        return 0.7

    def check_prerequisites(self) -> List[str]:
        missing = []
        if not have_tool("opa"):
            missing.append("bin:opa")
        return missing

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
