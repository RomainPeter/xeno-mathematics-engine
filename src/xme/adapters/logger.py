"""
Adaptateur de logging vers PCAP.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from xme.pcap.model import PCAPEntry
from xme.pcap.store import PCAPStore


def log_action(
    store: PCAPStore,
    action: str,
    actor: str = "xme",
    level: str = "S0",
    psp_ref: Optional[str] = None,
    obligations: Optional[Dict[str, str]] = None,
    deltas: Optional[Dict[str, float]] = None,
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
        timestamp=datetime.now(timezone.utc),
    )
    return store.append(entry)


def log_verdict(
    store: PCAPStore,
    obligation_id: str,
    level: str,
    ok: bool,
    details: Dict[str, Any],
    actor: str = "xme",
) -> PCAPEntry:
    """
    Log un verdict de vérification dans le store PCAP.

    Args:
        store: Store PCAP pour l'écriture
        obligation_id: ID de l'obligation vérifiée
        level: Niveau de sécurité (S0, S1, S2)
        ok: Résultat de la vérification (True/False)
        details: Détails de la vérification
        actor: Acteur qui effectue la vérification

    Returns:
        Entry PCAP créée
    """
    # Créer les obligations avec le verdict
    obligations = {obligation_id: str(ok)}

    # Créer les deltas avec les détails
    deltas = {f"verdict_{obligation_id}": 1.0 if ok else 0.0, f"level_{level}": 1.0}

    # Ajouter les détails comme obligations supplémentaires
    for key, value in details.items():
        if isinstance(value, (str, int, float, bool)):
            obligations[f"{obligation_id}_{key}"] = str(value)

    entry = PCAPEntry(
        action="verification_verdict",
        actor=actor,
        level=level,
        obligations=obligations,
        deltas=deltas,
        timestamp=datetime.now(timezone.utc),
    )
    return store.append(entry)
