from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Incident:
    """Represents an incident requiring capability handling."""

    id: str
    type: str
    severity: str = "info"  # info|low|medium|high|critical
    context: Dict[str, Any] = field(default_factory=dict)
    evidence_refs: List[str] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)  # K_sub
    V_target: Dict[str, float] = field(default_factory=dict)  # desired costs


@dataclass
class CapabilityResult:
    """Result from capability execution."""

    handler_id: str
    status: str  # planned|ok|rejected|error
    proofs: List[Dict[str, Any]]  # Proof-Carrying Action plans (not executed here)
    messages: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
