"""
Proof-Carrying Notation (PCN) - Symbol Forge.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import orjson
from pydantic import BaseModel, Field


class SymbolEntry(BaseModel):
    """Entrée de symbole dans le PCN."""

    concept_id: str
    symbol: str
    version: int = 1
    proof_ref: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SymbolStore:
    """Store pour les symboles PCN."""

    def __init__(self, path: Path):
        self.path = path
        self._state: Dict[str, Any] = {"symbols": []}  # list[SymbolEntry]
        self._load()

    def _load(self):
        """Charge les symboles depuis le fichier."""
        if self.path.exists():
            raw = orjson.loads(self.path.read_bytes())
            self._state["symbols"] = [SymbolEntry(**s) for s in raw.get("symbols", [])]
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._save()

    def _save(self):
        """Sauvegarde les symboles dans le fichier."""
        payload = {"symbols": [s.model_dump() for s in self._state["symbols"]]}
        self.path.write_bytes(orjson.dumps(payload, option=orjson.OPT_SORT_KEYS))

    def propose(self, concept_id: str, symbol: str, proof_ref: Optional[str]) -> SymbolEntry:
        """Propose un nouveau symbole avec preuve."""
        entry = SymbolEntry(concept_id=concept_id, symbol=symbol, proof_ref=proof_ref)
        self._state["symbols"].append(entry)
        self._save()
        return entry

    def list(self) -> List[SymbolEntry]:
        """Retourne la liste de tous les symboles."""
        return list(self._state["symbols"])
