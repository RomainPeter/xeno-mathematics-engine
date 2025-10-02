"""
État de l'orchestrator et gestion des budgets.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any


@dataclass
class Budgets:
    """Budgets temporels pour les opérations."""
    ae_ms: int = 1500
    cegis_ms: int = 0


@dataclass
class RunState:
    """État d'une exécution orchestrator."""
    run_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    budgets: Budgets = field(default_factory=Budgets)
    metrics: Dict[str, Any] = field(default_factory=dict)
