from __future__ import annotations

from typing import Any, Dict, List

from pefc.capabilities.core import Capability
from pefc.pcap.model import PCAP, ProofSpec, VVector
from pefc.pcap.utils import canonical_hash, sum_v


class CapabilityManager:
    """Manager for orchestrating proof generation capabilities."""

    def __init__(self, capabilities: List[Capability]):
        self.capabilities = capabilities

    def plan_pcap(
        self,
        *,
        action: str,
        incident: Dict[str, Any],
        obligations: List[str] | None = None,
        ctx: Dict[str, Any] | None = None,
    ) -> PCAP:
        """Plan a Proof-Carrying Action Plan for incident."""
        obligations = obligations or []
        ctx_hash = canonical_hash({"incident": incident, "obligations": obligations})
        selected: List[Capability] = [c for c in self.capabilities if c.can_handle(incident)]
        proofs: List[ProofSpec] = []
        vparts: List[Dict[str, float]] = []
        for c in selected:
            p = c.plan(incident, ctx or {})
            if p:
                proofs.extend(p)
                vparts.append(c.meta.cost_hint_V)
        v = VVector(
            **{
                k: v
                for k, v in sum_v(*vparts).items()
                if k in ("time", "audit_cost", "security_risk", "tech_debt")
            },
            extra={
                k: v
                for k, v in sum_v(*vparts).items()
                if k not in ("time", "audit_cost", "security_risk", "tech_debt")
            },
        )
        return PCAP(
            action=action,
            context_hash=ctx_hash,
            obligations=obligations,
            justification=v,
            proofs=proofs,
            meta={"capabilities": [c.meta.id for c in selected]},
        )
