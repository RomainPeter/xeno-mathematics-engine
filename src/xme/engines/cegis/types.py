"""
Types pour le moteur CEGIS (Counter-Example Guided Inductive Synthesis).
"""
from __future__ import annotations
from typing import Dict, Any, Literal, List, Optional


# Types de base pour CEGIS
Candidate = Dict[str, Any]
Verdict = Literal["ok", "fail"]
Counterexample = Dict[str, Any]


class CEGISResult:
    """Résultat d'une exécution CEGIS."""
    
    def __init__(
        self, 
        candidate: Optional[Candidate] = None,
        iters: int = 0,
        ok: bool = False,
        reason: str = ""
    ):
        self.candidate = candidate
        self.iters = iters
        self.ok = ok
        self.reason = reason
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation."""
        return {
            "candidate": self.candidate,
            "iters": self.iters,
            "ok": self.ok,
            "reason": self.reason
        }


class CEGISState:
    """État interne du moteur CEGIS."""
    
    def __init__(self, domain_state: Any = None):
        self.domain_state = domain_state
        self.iterations = 0
        self.candidates: List[Candidate] = []
        self.counterexamples: List[Counterexample] = []
    
    def add_candidate(self, candidate: Candidate) -> None:
        """Ajoute un candidat à l'historique."""
        self.candidates.append(candidate)
    
    def add_counterexample(self, ce: Counterexample) -> None:
        """Ajoute un contre-exemple à l'historique."""
        self.counterexamples.append(ce)
    
    def increment_iterations(self) -> None:
        """Incrémente le compteur d'itérations."""
        self.iterations += 1
