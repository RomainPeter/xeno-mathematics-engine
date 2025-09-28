from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Protocol
from pefc.pcap.model import ProofSpec


@dataclass
class CapMeta:
    """Metadata for a capability."""

    id: str
    version: str = "0.1.0"
    provides: List[str] = field(
        default_factory=list
    )  # ex: ["policy.proof", "trace.graph", "tests.synthetic"]
    prerequisites: List[str] = field(default_factory=list)
    cost_hint_V: Dict[str, float] = field(default_factory=dict)


class Capability(Protocol):
    """Protocol for proof generation capabilities."""

    @property
    def meta(self) -> CapMeta:
        """Get capability metadata."""
        ...

    def can_handle(self, incident: Dict[str, Any]) -> bool:
        """Check if capability can handle incident."""
        ...

    def plan(
        self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None
    ) -> List[ProofSpec]:
        """Plan proof generation for incident."""
        ...


# Capability categories (aliases)
class ProofGenerator(Capability):
    """Protocol for proof generators."""

    ...


class TestSynthesizer(Capability):
    """Protocol for test synthesizers."""

    ...


class PolicyUpdater(Capability):
    """Protocol for policy updaters."""

    ...
