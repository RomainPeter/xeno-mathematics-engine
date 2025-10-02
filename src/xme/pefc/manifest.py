"""
Manifest v1 pour Audit Pack avec calculs SHA256 et Merkle.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path
import hashlib
import orjson


class FileEntry(BaseModel):
    """Entrée de fichier dans le manifest."""
    path: str
    kind: str  # "psp", "pcap", "schema", "sbom", etc.
    size: int
    sha256: str


class Manifest(BaseModel):
    """Manifest v1 de l'Audit Pack."""
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tool: str = "xme"
    run_path: Optional[str] = None
    files: List[FileEntry] = Field(default_factory=list)
    merkle_root: str = ""
    notes: Optional[str] = None
    signatures: Optional[Dict[str, str]] = None

    def model_dump_json(self, **kwargs) -> str:
        """Sérialisation JSON canonique."""
        return orjson.dumps(self.model_dump(), option=orjson.OPT_SORT_KEYS).decode()


def calc_file_sha256(path: Path) -> str:
    """
    Calcule le SHA256 d'un fichier.
    
    Args:
        path: Chemin vers le fichier
    
    Returns:
        Hash SHA256 en hexadécimal
    """
    sha256_hash = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def build_merkle(leaves: List[str]) -> str:
    """
    Construit l'arbre de Merkle à partir des feuilles.
    
    Args:
        leaves: Liste des hashes SHA256 des feuilles
    
    Returns:
        Root de l'arbre de Merkle
    """
    if not leaves:
        return ""
    
    if len(leaves) == 1:
        return leaves[0]
    
    # Construire l'arbre niveau par niveau
    level = leaves[:]
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            combined = left + right
            next_level.append(hashlib.sha256(combined.encode("utf-8")).hexdigest())
        level = next_level
    
    return level[0]
