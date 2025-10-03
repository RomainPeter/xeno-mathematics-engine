"""
Deterministic pack builder: collect inputs, normalize, and produce manifest/merkle.
"""

from __future__ import annotations

import fnmatch
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pefc.events.manifest import (build_merkle_dataset_from_manifest,
                                  create_audit_manifest)


@dataclass
class PackConfig:
    inputs_files: List[str]
    inputs_globs: List[str]
    inputs_dirs: List[str]
    allow_outside_workspace: bool = False


def _workspace_root() -> Path:
    # Assume current repo root = cwd
    return Path(os.getcwd()).resolve()


def _iter_inputs(cfg: PackConfig, workspace: Path) -> List[Path]:
    selected: List[Path] = []
    # Files
    for f in cfg.inputs_files:
        p = (workspace / f).resolve() if not Path(f).is_absolute() else Path(f)
        selected.append(p)
    # Globs
    for g in cfg.inputs_globs:
        for p in sorted(workspace.rglob("*")):
            if p.is_file() and fnmatch.fnmatch(str(p.relative_to(workspace)), g):
                selected.append(p.resolve())
    # Dirs
    for d in cfg.inputs_dirs:
        base = (workspace / d).resolve() if not Path(d).is_absolute() else Path(d)
        for p in sorted(base.rglob("*")):
            if p.is_file():
                selected.append(p.resolve())
    # Deduplicate while preserving order
    seen = set()
    out: List[Path] = []
    for p in selected:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _enforce_workspace(paths: List[Path], workspace: Path) -> None:
    for p in paths:
        try:
            p.relative_to(workspace)
        except Exception:
            raise RuntimeError(f"Path outside workspace: {p}")


def _normalize_copy(src: Path, dst: Path, sde: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Read as text if likely text; fallback to binary copy
    try:
        data = src.read_text(encoding="utf-8", errors="strict")
        # Normalize line endings to LF
        data = "\n".join(data.splitlines())
        dst.write_text(data + ("\n" if data else ""), encoding="utf-8")
    except Exception:
        shutil.copyfile(src, dst)
    # Set mtime deterministically
    os.utime(dst, (sde, sde))


def build_pack(
    config_path: Path,
    audit_dir: Path,
    run_id: str,
    seed: Optional[int] = None,
) -> Dict[str, str]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    cfg_json = json.loads(config_path.read_text())
    cfg = PackConfig(
        inputs_files=cfg_json.get("inputs", {}).get("files", []),
        inputs_globs=cfg_json.get("inputs", {}).get("globs", []),
        inputs_dirs=cfg_json.get("inputs", {}).get("dirs", []),
        allow_outside_workspace=bool(cfg_json.get("allow_outside_workspace", False)),
    )
    if not (cfg.inputs_files or cfg.inputs_globs or cfg.inputs_dirs):
        raise RuntimeError("Empty inputs configuration")

    workspace = _workspace_root()
    inputs = _iter_inputs(cfg, workspace)
    if not cfg.allow_outside_workspace:
        _enforce_workspace(inputs, workspace)

    # Prepare output layout
    run_dir = audit_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "pcaps").mkdir(exist_ok=True)

    # Deterministic time
    sde = int(os.environ.get("SOURCE_DATE_EPOCH", "1700000000"))

    # Copy inputs under run_dir/inputs/ in sorted lexicographic order of relative paths
    inputs_root = run_dir / "inputs"
    pairs: List[Tuple[Path, Path]] = []
    for src in inputs:
        rel = None
        try:
            rel = src.relative_to(workspace)
        except Exception:
            rel = Path(src.name)
        dst = inputs_root / rel
        pairs.append((src, dst))
    pairs.sort(key=lambda t: str(t[1]).lower())
    for src, dst in pairs:
        _normalize_copy(src, dst, sde)

    # Provenance (SLSA-lite / in-toto minimal)
    lock_path = workspace / "requirements.lock"
    lock_hash = None
    if lock_path.exists():
        import hashlib

        h = hashlib.sha256()
        h.update(lock_path.read_bytes())
        lock_hash = h.hexdigest()

    inputs_rel = [str(p[1].relative_to(run_dir)).replace("\\", "/") for p in pairs]
    provenance = {
        "_format": "in-toto-statement-lite",
        "subject": {
            "name": run_id,
            "merkle_root": None,  # filled after manifest
        },
        "predicateType": "slsa-lite@v1",
        "predicate": {
            "builder": {
                "name": "pefc.pack",
            },
            "invocation": {
                "env": {
                    "SOURCE_DATE_EPOCH": sde,
                    "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"),
                    "TZ": os.environ.get("TZ"),
                },
                "parameters": {
                    "seed": seed,
                    "allow_outside_workspace": cfg.allow_outside_workspace,
                },
            },
            "materials": {
                "requirements_lock": {
                    "path": str(lock_path) if lock_path.exists() else None,
                    "sha256": lock_hash,
                }
            },
            "inputs": inputs_rel,
        },
    }
    (run_dir / "provenance.json").write_text(json.dumps(provenance, indent=2))

    # Empty logs/incidents if not provided by the run
    for name in ("logs.jsonl", "incidents.jsonl"):
        p = run_dir / name
        if not p.exists():
            p.write_text("")

    # Manifest + Merkle (over whole run_dir)
    manifest = create_audit_manifest(run_id=run_id, audit_dir=str(run_dir))
    (run_dir / "manifest.json").write_text(json.dumps(manifest.to_dict(), indent=2))
    # Back-fill provenance subject merkle root
    prov_obj = json.loads((run_dir / "provenance.json").read_text())
    prov_obj["subject"]["merkle_root"] = manifest.merkle_root
    (run_dir / "provenance.json").write_text(json.dumps(prov_obj, indent=2))
    # Build full merkle dataset (order, leaves, proofs)
    merkle_ds = build_merkle_dataset_from_manifest(manifest)
    (run_dir / "merkle.json").write_text(json.dumps(merkle_ds, indent=2))

    # Deterministic placeholder verdict (can be produced by orchestrator in real runs)
    verdict = {
        "run_id": run_id,
        "status": "unknown",
        "merkle_root": manifest.merkle_root,
        "inputs_count": len(inputs_rel),
    }
    (run_dir / "verdict.json").write_text(json.dumps(verdict, indent=2))

    return {"run_dir": str(run_dir), "merkle_root": manifest.merkle_root}
