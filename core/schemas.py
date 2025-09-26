"""
Schémas Pydantic pour le Proof Engine for Code v0.
Définit les structures de données centrales: Χ, J, PCAP, V.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class VJustification(BaseModel):
    """Vecteur de coûts et justifications pour une action."""
    time_ms: int = 0
    backtracks: int = 0
    audit_cost_ms: int = 0
    tech_debt: int = 0
    llm_time_ms: Optional[int] = None
    model: Optional[str] = None


class PCAP(BaseModel):
    """Proof-Carrying Action - Action avec preuves."""
    ts: str
    operator: str  # "plan" | "generate" | "apply" | "verify" | "rollback" | "replan"
    case_id: str
    pre: Dict[str, Any]
    post: Dict[str, Any]
    obligations: List[str]
    justification: VJustification
    proof_state_hash: str
    toolchain: Dict[str, str]
    llm_meta: Optional[Dict[str, Any]] = None
    verdict: Optional[str] = None  # "pass" | "fail"


class XState(BaseModel):
    """État hybride Χ du système."""
    H: List[str] = []  # hypothèses ou objectifs décrits textuellement
    E: List[str] = []  # evidences (tests passés, rapports)
    K: List[str] = []  # obligations/contraintes actives
    J: List[PCAP] = []  # journal structuré
    A: List[str] = []  # artefacts (patch ids, fichiers)
    Sigma: Dict[str, Any] = {}  # seed/env


class PlanProposal(BaseModel):
    """Proposition de plan du planificateur métacognitif."""
    plan: List[str]
    est_success: float = Field(ge=0.0, le=1.0)
    est_cost: float
    notes: str
    llm_meta: Optional[Dict[str, Any]] = None


class PatchProposal(BaseModel):
    """Proposition de patch du générateur stochastique."""
    patch_unified: str
    rationale: str
    predicted_obligations_satisfied: List[str]
    risk_score: float = Field(ge=0.0, le=1.0)
    notes: str
    llm_meta: Optional[Dict[str, Any]] = None


class ObligationResults(BaseModel):
    """Résultats des vérifications d'obligations."""
    tests_ok: bool
    lint_ok: bool
    types_ok: bool
    security_ok: bool
    complexity_ok: bool
    docstring_ok: bool
    
    def violations_count(self) -> int:
        """Compte le nombre de violations."""
        return sum(1 for v in self.model_dump().values() if not v)
    
    def all_passed(self) -> bool:
        """Vérifie si toutes les obligations sont satisfaites."""
        return self.violations_count() == 0


class DeltaMetrics(BaseModel):
    """Métriques δ (écart entre intention et résultat)."""
    dH: float = Field(ge=0.0, le=1.0)  # distance sur les hypothèses
    dE: float = Field(ge=0.0, le=1.0)  # distance sur les évidences
    dK: float = Field(ge=0.0, le=1.0)  # distance sur les obligations
    dAST: float = Field(ge=0.0, le=1.0)  # divergence AST
    violations_penalty: float = Field(ge=0.0, le=1.0)  # pénalité pour violations
    delta_total: float = Field(ge=0.0, le=1.0)  # delta combiné
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class Attestation(BaseModel):
    """Attestation de vérification."""
    ts: float
    pcap_count: int
    verdicts: List[Dict[str, Any]]
    digest: str
    signature: Optional[str] = None  # Ed25519 signature (optionnel)