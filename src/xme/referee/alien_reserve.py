"""
Alien Reserves - Embargo des X-lineages.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import orjson


class AlienReserve:
    """Gestion des embargos sur les X-lineages."""

    def __init__(self, path: Path):
        self.path = path
        self._state: Dict[str, Any] = {
            "lineages": {}
        }  # lineage_id -> {meta, embargoed:bool, created_at, released_at?}
        self._load()

    def _load(self) -> None:
        """Charge l'état depuis le fichier."""
        if self.path.exists():
            self._state = orjson.loads(self.path.read_bytes())
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._save()

    def _save(self) -> None:
        """Sauvegarde l'état dans le fichier."""
        self.path.write_bytes(orjson.dumps(self._state, option=orjson.OPT_SORT_KEYS))

    def register(self, lineage_id: str, meta: Optional[Dict] = None) -> None:
        """Enregistre un lineage avec embargo."""
        now = datetime.now(timezone.utc).isoformat()
        self._state["lineages"][lineage_id] = {
            "embargoed": True,
            "meta": meta or {},
            "created_at": now,
        }
        self._save()

    def is_embargoed(self, lineage_id: str) -> bool:
        """Vérifie si un lineage est sous embargo."""
        info = self._state["lineages"].get(lineage_id)
        return bool(info and info.get("embargoed", False))

    def release(self, lineage_id: str, reason: str) -> bool:
        """Libère un lineage de l'embargo."""
        if lineage_id not in self._state["lineages"]:
            return False
        self._state["lineages"][lineage_id]["embargoed"] = False
        self._state["lineages"][lineage_id]["released_at"] = datetime.now(timezone.utc).isoformat()
        self._state["lineages"][lineage_id]["release_reason"] = reason
        self._save()
        return True

    def list(self) -> Dict[str, Dict]:
        """Retourne la liste de tous les lineages."""
        return self._state["lineages"]
