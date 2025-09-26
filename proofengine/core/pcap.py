"""Utility helpers for Proof-Carrying Action (PCAP) files."""

from __future__ import annotations

import glob
import hashlib
import json
import os
import time
from typing import Dict, List

from .schemas import PCAP


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def merkle_of(obj: Dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode("utf-8")).hexdigest()


def write_pcap(entry: PCAP, out_dir: str = "out/pcap") -> str:
    os.makedirs(out_dir, exist_ok=True)
    digest = merkle_of(entry.to_dict())
    path = os.path.join(out_dir, f"{int(time.time()*1000)}_{digest[:8]}.json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(entry.to_json())
    return path


def read_pcap(path: str) -> PCAP:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return PCAP.model_validate(payload)


def list_pcaps(directory: str = "out/pcap") -> List[str]:
    pattern = os.path.join(directory, "*.json")
    return sorted(glob.glob(pattern))


def verify_pcap_chain(directory: str = "out/pcap") -> Dict[str, object]:
    files = list_pcaps(directory)
    if not files:
        return {"status": "empty", "count": 0, "files": []}

    errors: List[str] = []
    verified: List[str] = []

    for path in files:
        try:
            read_pcap(path)
            verified.append(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{os.path.basename(path)}: {exc}")

    if errors:
        return {"status": "error", "count": len(files), "files": verified, "errors": errors}

    return {"status": "ok", "count": len(files), "files": verified}

