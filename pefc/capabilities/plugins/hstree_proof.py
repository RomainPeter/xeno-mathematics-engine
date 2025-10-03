from __future__ import annotations

from typing import Any, Dict, List

from pefc.capabilities.core import CapMeta
from pefc.pcap.model import ProofSpec


class HSTreeProofGenerator:
    """HS-Tree proof generator capability."""

    def __init__(self, emit_dot: bool = True):
        self._meta = CapMeta(
            id="cap-hstree",
            provides=["trace.graph"],
            prerequisites=[],
            cost_hint_V={"audit_cost": 0.3, "time": 0.2},
        )
        self.emit_dot = emit_dot

    @property
    def meta(self):
        return self._meta

    def can_handle(self, incident: Dict[str, Any]) -> bool:
        return incident.get("type") in ("traceability.gap", "security.policy.violation")

    def plan(self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None) -> List[ProofSpec]:
        refs = incident.get("evidence_refs", [])
        steps = [
            {"op": "build_tree", "inputs": {"evidence_refs": refs}},
            {"op": "check_connectivity"},
        ]
        if self.emit_dot:
            steps.append({"op": "emit_dot"})
        return [
            ProofSpec(
                type="hs-tree",
                args={"steps": steps},
                expect={"connected": True},
            )
        ]
