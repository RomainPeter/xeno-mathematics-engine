"""
Adaptateur de logging vers PCAP.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from xme.pcap.store import PCAPStore
from xme.pcap.model import PCAPEntry


def log_action(
    store: PCAPStore, 
    action: str, 
    actor: str = "xme", 
    level: str = "S0",
    psp_ref: Optional[str] = None, 
    obligations: Optional[Dict[str, str]] = None,
    deltas: Optional[Dict[str, float]] = None
) -> PCAPEntry:
    """
    Log une action dans le store PCAP.
    
    Args:
        store: Store PCAP pour l'écriture
        action: Nom de l'action
        actor: Acteur qui effectue l'action
        level: Niveau de sécurité (S0, S1, S2)
        psp_ref: Référence vers un PSP
        obligations: Obligations associées
        deltas: Deltas de métriques
    
    Returns:
        Entry PCAP créée
    """
    entry = PCAPEntry(
        action=action, 
        actor=actor, 
        level=level, 
        psp_ref=psp_ref,
        obligations=obligations or {}, 
        deltas=deltas or {},
        timestamp=datetime.now(timezone.utc)
    )
    return store.append(entry)
