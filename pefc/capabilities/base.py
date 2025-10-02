from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


@dataclass
class CapabilityMetadata:
    """Metadata for a capability handler."""

    id: str
    version: str = "0.1.0"
    provides: List[str] = field(default_factory=list)  # supported incident types
    prerequisites: List[str] = field(default_factory=list)  # ex: ["bin:opa"]
    cost_hint_V: Dict[str, float] = field(default_factory=dict)  # ex: {"audit_cost": 0.2}


class IncidentHandler(Protocol):
    """Protocol for incident handling capabilities."""

    @property
    def meta(self) -> CapabilityMetadata:
        """Get capability metadata."""
        ...

    def can_handle(self, incident_type: str) -> bool:
        """Check if handler can handle incident type."""
        ...

    def score(self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None) -> float:
        """Score incident for priority (higher = better)."""
        ...

    def check_prerequisites(self) -> List[str]:
        """Check prerequisites and return missing ones."""
        ...

    def handle(self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Handle incident and return result."""
        ...


def have_tool(bin_name: str) -> bool:
    """Check if a tool is available in PATH."""
    return shutil.which(bin_name) is not None
