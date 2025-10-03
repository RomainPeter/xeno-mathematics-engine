from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class VVector(BaseModel):
    """Vector of additive costs; free keys but bounded."""

    time: float | None = None
    audit_cost: float | None = None
    security_risk: float | None = None
    tech_debt: float | None = None
    extra: Dict[str, float] = Field(default_factory=dict)


class ProofSpec(BaseModel):
    """Specification for a proof to be generated."""

    type: str
    args: Dict[str, Any] = Field(default_factory=dict)
    expect: Dict[str, Any] = Field(default_factory=dict)


class PCAP(BaseModel):
    """Proof-Carrying Action Plan."""

    action: str
    context_hash: str
    obligations: List[str] = Field(default_factory=list)
    justification: VVector = Field(default_factory=VVector)
    proofs: List[ProofSpec] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
