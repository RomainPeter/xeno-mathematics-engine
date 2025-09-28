from __future__ import annotations
from typing import Dict, Any, List
from pefc.capabilities.core import CapMeta
from pefc.pcap.model import ProofSpec


class SimplePolicyUpdater:
    """Simple policy updater capability."""

    def __init__(self, output_dir: str = "policies/patches"):
        self._meta = CapMeta(
            id="cap-policy-update",
            provides=["policy.update"],
            prerequisites=[],
            cost_hint_V={"tech_debt": -0.1},
        )
        self.output_dir = output_dir

    @property
    def meta(self):
        return self._meta

    def can_handle(self, incident: Dict[str, Any]) -> bool:
        return incident.get("type") in ("security.policy.violation", "compliance.check")

    def plan(
        self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None
    ) -> List[ProofSpec]:
        rule = {"deny_if": incident.get("context", {}).get("pattern", "*")}
        return [
            ProofSpec(
                type="policy.patch",
                args={"output_dir": self.output_dir, "rule": rule},
                expect={"patched": True},
            )
        ]
