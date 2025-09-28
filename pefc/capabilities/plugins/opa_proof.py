from __future__ import annotations
from typing import Dict, Any, List
from pefc.capabilities.core import CapMeta
from pefc.pcap.model import ProofSpec


class OPAProofGenerator:
    """OPA Rego proof generator capability."""

    def __init__(self, policy_dir: str = "policies", query: str = "data.pefc.allow"):
        self._meta = CapMeta(
            id="cap-opa-proof",
            provides=["policy.proof"],
            prerequisites=["bin:opa"],
            cost_hint_V={"audit_cost": 0.2, "time": 0.1},
        )
        self.policy_dir = policy_dir
        self.query = query

    @property
    def meta(self):
        return self._meta

    def can_handle(self, incident: Dict[str, Any]) -> bool:
        return incident.get("type") in ("security.policy.violation", "compliance.check")

    def plan(
        self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None
    ) -> List[ProofSpec]:
        input_doc = {"incident": incident, "ctx": ctx or {}}
        return [
            ProofSpec(
                type="opa.eval",
                args={
                    "policy_dir": self.policy_dir,
                    "query": self.query,
                    "input": input_doc,
                },
                expect={"allow": False},
            )
        ]
