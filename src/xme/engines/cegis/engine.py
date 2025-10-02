"""
Moteur CEGIS générique (Counter-Example Guided Inductive Synthesis).
"""
from __future__ import annotations
from typing import Protocol, Any, Tuple
from .types import Candidate, Verdict, Counterexample, CEGISResult, CEGISState


class CEGISDomain(Protocol):
    """Interface pour un domaine CEGIS."""
    
    def propose(self, state: Any) -> Candidate:
        """Propose un candidat basé sur l'état actuel."""
        ...
    
    def verify(self, candidate: Candidate) -> Tuple[Verdict, Optional[Counterexample]]:
        """Vérifie un candidat et retourne verdict + contre-exemple si échec."""
        ...
    
    def refine(self, state: Any, counterexample: Counterexample) -> Any:
        """Raffine l'état avec un contre-exemple."""
        ...


class CEGISEngine:
    """Moteur CEGIS générique."""
    
    def __init__(self, domain: CEGISDomain):
        self.domain = domain
        self.state = CEGISState()
    
    def run(self, max_iter: int, initial_state: Any = None) -> CEGISResult:
        """
        Exécute la boucle CEGIS jusqu'à convergence ou limite d'itérations.
        
        Args:
            max_iter: Nombre maximum d'itérations
            initial_state: État initial du domaine
        
        Returns:
            Résultat avec candidat final, nombre d'itérations, et statut
        """
        if initial_state is not None:
            self.state.domain_state = initial_state
        
        for iteration in range(max_iter):
            self.state.increment_iterations()
            
            # Phase propose
            candidate = self.domain.propose(self.state.domain_state)
            self.state.add_candidate(candidate)
            
            # Phase verify
            verdict, counterexample = self.domain.verify(candidate)
            
            if verdict == "ok":
                # Succès : candidat valide trouvé
                return CEGISResult(
                    candidate=candidate,
                    iters=self.state.iterations,
                    ok=True,
                    reason="converged"
                )
            
            # Phase refine
            if counterexample is not None:
                self.state.add_counterexample(counterexample)
                self.state.domain_state = self.domain.refine(
                    self.state.domain_state, 
                    counterexample
                )
            else:
                # Pas de contre-exemple disponible
                return CEGISResult(
                    candidate=candidate,
                    iters=self.state.iterations,
                    ok=False,
                    reason="no_counterexample"
                )
        
        # Limite d'itérations atteinte
        return CEGISResult(
            candidate=self.state.candidates[-1] if self.state.candidates else None,
            iters=self.state.iterations,
            ok=False,
            reason="max_iterations_reached"
        )
    
    def reset(self) -> None:
        """Remet à zéro l'état du moteur."""
        self.state = CEGISState()
