"""
Gestion de l'état hybride Χ avec snapshots et rollback.
Système de journalisation append-only avec hachage d'état.
"""

import copy
from typing import Any, Dict, List, Optional, Set
from .schemas import PCAP, XState
from .hashing import hash_state, create_state_snapshot, restore_state_from_snapshot


class StateManager:
    """Gestionnaire d'état avec snapshots et rollback."""
    
    def __init__(self, initial_state: XState):
        self.current_state = initial_state
        self.snapshots: List[Dict[str, Any]] = []
        self.journal: List[PCAP] = []
        self.refusal_sets: List[Dict[str, Any]] = []
    
    def snapshot(self) -> str:
        """Crée un snapshot de l'état actuel."""
        snapshot = create_state_snapshot(self.current_state)
        self.snapshots.append(snapshot)
        return f"snapshot_{len(self.snapshots) - 1}"
    
    def rollback(self, snapshot_id: Optional[str] = None) -> bool:
        """
        Restaure l'état à un snapshot précédent.
        Si snapshot_id est None, restaure le dernier snapshot.
        """
        if not self.snapshots:
            return False
        
        if snapshot_id is None:
            # Restaurer le dernier snapshot
            snapshot = self.snapshots[-1]
        else:
            # Trouver le snapshot par ID
            try:
                idx = int(snapshot_id.split('_')[1])
                if idx >= len(self.snapshots):
                    return False
                snapshot = self.snapshots[idx]
            except (ValueError, IndexError):
                return False
        
        self.current_state = restore_state_from_snapshot(snapshot)
        return True
    
    def append_journal(self, pcap: PCAP) -> None:
        """Ajoute un PCAP au journal (append-only)."""
        self.journal.append(pcap)
        # Mettre à jour l'état avec la référence au PCAP
        self.current_state.J.append(pcap.pcap_hash)
        # Recalculer le hash d'état
        self.current_state.state_hash = hash_state(self.current_state)
    
    def add_rule_from_incident(self, incident: PCAP, rule_type: str = "forbidden") -> None:
        """
        Ajoute une règle basée sur un incident.
        Types: "forbidden", "required", "conditional"
        """
        rule = {
            "type": rule_type,
            "trigger": incident.action,
            "context": incident.obligations,
            "justification": incident.justification.to_dict(),
            "created_from": incident.pcap_hash,
            "timestamp": incident.ts.isoformat()
        }
        
        self.current_state.K.append(rule)
        self.current_state.state_hash = hash_state(self.current_state)
    
    def get_refusal_set(self) -> List[Dict[str, Any]]:
        """Retourne l'ensemble des actions interdites."""
        return [rule for rule in self.current_state.K if rule.get("type") == "forbidden"]
    
    def is_action_forbidden(self, action: str) -> bool:
        """Vérifie si une action est interdite."""
        refusal_set = self.get_refusal_set()
        return any(rule["trigger"] == action for rule in refusal_set)
    
    def get_state_hash(self) -> str:
        """Retourne le hash de l'état actuel."""
        return self.current_state.state_hash
    
    def get_journal_hash(self) -> str:
        """Retourne le hash du journal."""
        from .hashing import hash_list
        return hash_list([pcap.pcap_hash for pcap in self.journal])
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de l'état."""
        return {
            "snapshots_count": len(self.snapshots),
            "journal_length": len(self.journal),
            "rules_count": len(self.current_state.K),
            "artifacts_count": len(self.current_state.A),
            "hypotheses_count": len(self.current_state.H),
            "evidences_count": len(self.current_state.E),
            "state_hash": self.current_state.state_hash,
            "journal_hash": self.get_journal_hash()
        }


def create_initial_state(
    hypotheses: Set[str] = None,
    evidences: Set[str] = None,
    obligations: List[Dict[str, Any]] = None,
    artifacts: List[str] = None,
    sigma: Dict[str, Any] = None
) -> XState:
    """Crée un état initial."""
    if hypotheses is None:
        hypotheses = set()
    if evidences is None:
        evidences = set()
    if obligations is None:
        obligations = []
    if artifacts is None:
        artifacts = []
    if sigma is None:
        sigma = {}
    
    state = XState(
        H=hypotheses,
        E=evidences,
        K=obligations,
        A=artifacts,
        J=[],
        Sigma=sigma,
        state_hash=""
    )
    
    # Calculer le hash initial
    state.state_hash = hash_state(state)
    return state


def merge_states(state1: XState, state2: XState) -> XState:
    """Fusionne deux états (pour les opérations de merge)."""
    merged = XState(
        H=state1.H.union(state2.H),
        E=state1.E.union(state2.E),
        K=state1.K + state2.K,
        A=state1.A + state2.A,
        J=state1.J + state2.J,
        Sigma={**state1.Sigma, **state2.Sigma},
        state_hash=""
    )
    
    merged.state_hash = hash_state(merged)
    return merged


def diff_states(old_state: XState, new_state: XState) -> Dict[str, Any]:
    """Calcule la différence entre deux états."""
    return {
        "H_added": new_state.H - old_state.H,
        "H_removed": old_state.H - new_state.H,
        "E_added": new_state.E - old_state.E,
        "E_removed": old_state.E - new_state.E,
        "K_added": len(new_state.K) - len(old_state.K),
        "A_added": new_state.A[len(old_state.A):],
        "J_added": new_state.J[len(old_state.J):]
    }
