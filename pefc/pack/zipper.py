from __future__ import annotations
from pathlib import Path
from typing import Optional, Set
from zipfile import ZipFile
import logging

log = logging.getLogger(__name__)


def add_to_zip(
    zipf: ZipFile,
    arcname: str,
    *,
    src_path: Optional[Path] = None,
    data: Optional[bytes] = None,
    seen: Set[str],
) -> bool:
    """
    Ajoute un fichier au zip si arcname pas déjà présent.
    - src_path XOR data (exactement un des deux)
    - Retourne True si écrit, False si ignoré (dup).
    """
    if arcname in seen:
        log.warning("zip: duplicate arcname ignored: %s", arcname)
        return False
    if (src_path is None) == (data is None):
        raise ValueError("add_to_zip requires exactly one of src_path or data")
    if data is not None:
        zipf.writestr(arcname, data)
    else:
        zipf.write(str(src_path), arcname)
    seen.add(arcname)
    return True


def dedup_additional_files(files: list[tuple[Path, str]], seen: Set[str]) -> list[tuple[Path, str]]:
    """
    files = [(src_path, arcname)]
    Filtre:
      - garde le premier arcname jamais vu
      - ignore ceux déjà en seen
      - ignore les doublons d'arcname dans 'files'
    """
    out: list[tuple[Path, str]] = []
    local_seen: Set[str] = set()
    for src, arc in files:
        if arc in seen:
            log.warning(
                "zip: additional file collides with existing arcname, ignored: %s (%s)",
                arc,
                src,
            )
            continue
        if arc in local_seen:
            log.warning("zip: duplicate additional arcname ignored: %s (%s)", arc, src)
            continue
        local_seen.add(arc)
        out.append((src, arc))
    return out


class ZipAdder:
    def __init__(self):
        self.seen: Set[str] = set()

    def add_file(self, z: ZipFile, src_path, arcname: str):
        if arcname in self.seen:
            raise RuntimeError(f"duplicate arcname: {arcname}")
        z.write(str(src_path), arcname)
        self.seen.add(arcname)

    def add_text(self, z: ZipFile, arcname: str, text: str):
        if arcname in self.seen:
            raise RuntimeError(f"duplicate arcname: {arcname}")
        z.writestr(arcname, text)
        self.seen.add(arcname)

    def add_bytes(self, z: ZipFile, arcname: str, data: bytes):
        if arcname in self.seen:
            raise RuntimeError(f"duplicate arcname: {arcname}")
        z.writestr(arcname, data)
        self.seen.add(arcname)
