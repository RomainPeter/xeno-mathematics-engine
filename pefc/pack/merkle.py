from __future__ import annotations
import hashlib
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, List, Dict, Tuple, Optional, BinaryIO
import time

CHUNK_SIZE = 1 << 20  # 1 MiB


@dataclass
class PackEntry:
    arcname: str  # path inside zip (POSIX, normalized)
    src_path: Path  # source file on disk
    size: int  # bytes
    sha256: str  # hex digest of content
    leaf: str  # hex digest of leaf hash


def _posix_norm(path: Path, base_dir: Optional[Path] = None) -> str:
    if base_dir:
        arc = Path(path).resolve().relative_to(base_dir.resolve())
    else:
        arc = path
    arc_str = str(PurePosixPath(arc.as_posix()))
    arc_str = unicodedata.normalize("NFC", arc_str)
    return arc_str


def _sha256_stream(fp: BinaryIO) -> str:
    h = hashlib.sha256()
    for chunk in iter(lambda: fp.read(CHUNK_SIZE), b""):
        h.update(chunk)
    return h.hexdigest()


def _u32be(n: int) -> bytes:
    return n.to_bytes(4, "big", signed=False)


def _u64be(n: int) -> bytes:
    return n.to_bytes(8, "big", signed=False)


def _leaf_hash(arcname: str, size: int, content_sha256_hex: str) -> str:
    path_bytes = arcname.encode("utf-8")
    cbytes = bytes.fromhex(content_sha256_hex)
    h = hashlib.sha256()
    h.update(b"leaf")
    h.update(_u32be(len(path_bytes)))
    h.update(path_bytes)
    h.update(_u64be(size))
    h.update(cbytes)
    return h.hexdigest()


def build_entries(paths: Iterable[Tuple[Path, str]]) -> List[PackEntry]:
    # paths: iterable of (src_path, arcname_hint_or_rel)
    entries: List[PackEntry] = []
    seen: set[str] = set()
    for src, arc_hint in paths:
        src = Path(src)
        if not src.is_file():
            continue
        arcname = str(PurePosixPath(arc_hint))
        arcname = unicodedata.normalize("NFC", arcname)
        if arcname in seen:
            raise RuntimeError(f"duplicate arcname: {arcname}")
        seen.add(arcname)
        size = src.stat().st_size
        with src.open("rb") as f:
            sha = _sha256_stream(f)
        leaf = _leaf_hash(arcname, size, sha)
        entries.append(PackEntry(arcname=arcname, src_path=src, size=size, sha256=sha, leaf=leaf))
    # sort by arcname for determinism
    entries.sort(key=lambda e: e.arcname)
    return entries


def _merkle_level(hashes: List[bytes]) -> List[bytes]:
    if not hashes:
        return []
    out: List[bytes] = []
    i = 0
    n = len(hashes)
    while i < n:
        left = hashes[i]
        if i + 1 < n:
            right = hashes[i + 1]
        else:
            right = left  # duplicate last
        h = hashlib.sha256()
        h.update(b"node")
        h.update(left)
        h.update(right)
        out.append(h.digest())
        i += 2
    return out


def compute_merkle_root(entries: List[PackEntry]) -> str:
    if not entries:
        # root of empty set: SHA256("empty")
        return hashlib.sha256(b"empty").hexdigest()
    leaves = [bytes.fromhex(e.leaf) for e in entries]
    level = leaves
    while len(level) > 1:
        level = _merkle_level(level)
    return level[0].hex()


def build_manifest(
    entries: List[PackEntry],
    merkle_root: str,
    pack_name: str,
    version: str,
    cli_version: str = "0.1.0",
    signature_info: Optional[Dict] = None,
) -> Dict:
    """Build complete manifest with all required fields."""
    import platform

    # Calculate total size (excluding manifest.json and merkle.txt)
    total_size = sum(e.size for e in entries if e.arcname not in {"manifest.json", "merkle.txt"})

    manifest = {
        "format_version": "1.0",
        "pack_name": pack_name,
        "version": version,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "builder": {"cli_version": cli_version, "host": platform.node()},
        "file_count": len(entries),
        "total_size_bytes": total_size,
        "merkle_root": merkle_root,
        "files": [
            {"path": e.arcname, "size": e.size, "sha256": e.sha256, "leaf": e.leaf} for e in entries
        ],
    }

    # Add signature info if provided
    if signature_info:
        manifest["signature"] = signature_info

    return manifest
