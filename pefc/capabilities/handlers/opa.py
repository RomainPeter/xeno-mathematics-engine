from __future__ import annotations
from typing import Dict, Any, List
from pefc.capabilities.base import CapabilityMetadata, have_tool
from pefc.incidents.types import CapabilityResult


class OPAHandler:
    """Handler for OPA Rego capability."""

    def __init__(
        self, policy_dir: str = "policies", query: str = "data.pefc.allow", **kw
    ):
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

    def score(
        self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None
    ) -> float:
        return 0.7

    def check_prerequisites(self) -> List[str]:
        missing = []
        if not have_tool("opa"):
            missing.append("bin:opa")
        return missing

    def handle(
        self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        input_doc = {"incident": incident, "ctx": ctx or {}}
        proofs = [
            {
                "type": "opa-eval",
                "policy_dir": self.policy_dir,
                "query": self.query,
                "input": input_doc,
                "expect": {"allow": False},  # e.g. incident should reproduce violation
            }
        ]
        return CapabilityResult(
            handler_id=self.meta.id,
            status="planned",
            proofs=proofs,
            messages=["opa plan"],
            meta={"policy_dir": self.policy_dir},
        ).__dict__
