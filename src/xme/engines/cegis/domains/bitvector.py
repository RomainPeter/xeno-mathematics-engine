"""
Domaine CEGIS pour la synthèse de vecteurs de bits secrets.
"""
from __future__ import annotations
from typing import Any, Tuple, Optional, List, Dict
from ..types import Candidate, Verdict, Counterexample


class BitvectorState:
    """État du domaine bitvector."""
    
    def __init__(self, length: int, known_bits: Optional[Dict[int, str]] = None):
        self.length = length
        self.known_bits = known_bits or {}
    
    def is_complete(self) -> bool:
        """Vérifie si tous les bits sont connus."""
        return len(self.known_bits) == self.length
    
    def get_candidate(self) -> str:
        """Construit un candidat à partir des bits connus."""
        result = []
        for i in range(self.length):
            if i in self.known_bits:
                result.append(self.known_bits[i])
            else:
                result.append("0")  # Valeur par défaut
        return "".join(result)


class BitvectorDomain:
    """Domaine CEGIS pour la synthèse de vecteurs de bits."""
    
    def __init__(self, secret: str):
        self.secret = secret
        self.length = len(secret)
    
    def propose(self, state: BitvectorState) -> Candidate:
        """
        Propose un candidat en complétant les bits inconnus avec 0.
        
        Args:
            state: État actuel avec bits connus
        
        Returns:
            Candidat sous forme de chaîne de bits
        """
        candidate = state.get_candidate()
        return {"bits": candidate}
    
    def verify(self, candidate: Candidate) -> Tuple[Verdict, Optional[Counterexample]]:
        """
        Vérifie un candidat en le comparant au secret.
        
        Args:
            candidate: Candidat à vérifier
        
        Returns:
            Tuple (verdict, contre-exemple)
        """
        candidate_bits = candidate["bits"]
        if candidate_bits == self.secret:
            return "ok", None
        
        # Trouver les positions où il y a un mismatch
        mismatches = []
        for i in range(min(len(candidate_bits), len(self.secret))):
            if candidate_bits[i] != self.secret[i]:
                mismatches.append(i)
        
        # Ajouter les positions manquantes si les longueurs diffèrent
        if len(candidate_bits) < len(self.secret):
            for i in range(len(candidate_bits), len(self.secret)):
                mismatches.append(i)
        elif len(candidate_bits) > len(self.secret):
            for i in range(len(self.secret), len(candidate_bits)):
                mismatches.append(i)
        
        return "fail", {"mismatch": mismatches}
    
    def refine(self, state: BitvectorState, counterexample: Counterexample) -> BitvectorState:
        """
        Raffine l'état en fixant les bits corrects.
        
        Args:
            state: État actuel
            counterexample: Contre-exemple avec positions de mismatch
        
        Returns:
            Nouvel état raffiné
        """
        new_known_bits = state.known_bits.copy()
        
        # Pour chaque position de mismatch, on sait que le bit candidat est incorrect
        # On peut donc exclure cette valeur pour cette position
        # Dans ce domaine simple, on fixe directement les bits corrects
        for pos in counterexample["mismatch"]:
            if pos < len(self.secret):
                # Fixer le bit correct
                new_known_bits[pos] = self.secret[pos]
        
        return BitvectorState(self.length, new_known_bits)
    
    def create_initial_state(self) -> BitvectorState:
        """Crée l'état initial vide."""
        return BitvectorState(self.length)
