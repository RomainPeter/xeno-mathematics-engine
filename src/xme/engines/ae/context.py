"""
Contexte FCA (Formal Concept Analysis) et chargement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set

import orjson
from pydantic import BaseModel


class FCAObject(BaseModel):
    """Objet FCA avec ses attributs."""

    id: str
    attrs: List[str]


class FCAContext(BaseModel):
    """Contexte FCA complet."""

    attributes: List[str]
    objects: List[FCAObject]

    def obj_attrs(self) -> Dict[str, Set[str]]:
        """Retourne un mapping objet -> attributs."""
        return {o.id: set(o.attrs) for o in self.objects}


def load_context(path: str | Path) -> FCAContext:
    """Charge un contexte FCA depuis un fichier JSON."""
    return FCAContext(**orjson.loads(Path(path).read_bytes()))
