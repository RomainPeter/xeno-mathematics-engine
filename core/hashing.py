"""
Système de hachage Merkle pour l'état hybride Χ et les PCAPs.
Génère des hashes déterministes pour snapshots et rollback.
"""

import hashlib
import json
from typing import Any, Dict, List, Set, Union
from .schemas import PCAP, XState


def hash_string(content: str) -> str:
    """Génère un hash SHA256 d'une chaîne."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def hash_dict(data: Dict[str, Any]) -> str:
    """Génère un hash d'un dictionnaire (ordre indépendant)."""
    # Tri des clés pour garantir l'ordre
    sorted_items = sorted(data.items())
    content = json.dumps(sorted_items, sort_keys=True, default=str)
    return hash_string(content)


def hash_set(items: Set[str]) -> str:
    """Génère un hash d'un set (ordre indépendant)."""
    # Tri des éléments pour garantir l'ordre
    sorted_items = sorted(items)
    content = json.dumps(sorted_items, sort_keys=True)
    return hash_string(content)


def hash_list(items: List[Any]) -> str:
    """Génère un hash d'une liste."""
    content = json.dumps(items, sort_keys=True, default=str)
    return hash_string(content)


def hash_state(X: XState) -> str:
    """
    Génère un hash Merkle-like de l'état hybride Χ.
    Inclut les versions des dépendances pour la reproductibilité.
    """
    # Hash des composants individuels
    h_H = hash_set(X.H)
    h_E = hash_set(X.E)
    h_K = hash_list(X.K)
    h_A = hash_list(X.A)
    h_J = hash_list(X.J)
    h_Sigma = hash_dict(X.Sigma)
    
    # Hash composite
    composite = {
        "H": h_H,
        "E": h_E,
        "K": h_K,
        "A": h_A,
        "J": h_J,
        "Sigma": h_Sigma
    }
    
    return hash_dict(composite)


def hash_pcap(pcap: PCAP) -> str:
    """Génère un hash canonique d'un PCAP."""
    # Exclure le hash du PCAP lui-même pour éviter la récursion
    pcap_dict = pcap.to_dict()
    pcap_dict.pop('pcap_hash', None)
    
    return hash_dict(pcap_dict)


def hash_patch(patch: str) -> str:
    """Génère un hash d'un patch."""
    return hash_string(patch)


def hash_artifacts(artifacts: List[str]) -> str:
    """Génère un hash des artefacts."""
    return hash_list(artifacts)


def verify_state_integrity(X: XState) -> bool:
    """Vérifie l'intégrité de l'état en recalculant le hash."""
    computed_hash = hash_state(X)
    return computed_hash == X.state_hash


def verify_pcap_integrity(pcap: PCAP) -> bool:
    """Vérifie l'intégrité d'un PCAP en recalculant le hash."""
    computed_hash = hash_pcap(pcap)
    return computed_hash == pcap.pcap_hash


def create_state_snapshot(X: XState) -> Dict[str, Any]:
    """Crée un snapshot sérialisable de l'état."""
    return {
        "H": list(X.H),
        "E": list(X.E),
        "K": X.K.copy(),
        "A": X.A.copy(),
        "J": X.J.copy(),
        "Sigma": X.Sigma.copy(),
        "state_hash": X.state_hash,
        "timestamp": X.Sigma.get("timestamp", "")
    }


def restore_state_from_snapshot(snapshot: Dict[str, Any]) -> XState:
    """Restaure un état à partir d'un snapshot."""
    return XState(
        H=set(snapshot["H"]),
        E=set(snapshot["E"]),
        K=snapshot["K"].copy(),
        A=snapshot["A"].copy(),
        J=snapshot["J"].copy(),
        Sigma=snapshot["Sigma"].copy(),
        state_hash=snapshot["state_hash"]
    )
