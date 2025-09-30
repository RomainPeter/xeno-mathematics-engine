#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", required=True, help="Path to produced artifacts directory")
    ap.add_argument("--baseline", required=True, help="Path to baseline merkle JSON")
    args = ap.parse_args()

    artifacts = Path(args.artifacts)
    baseline_path = Path(args.baseline)

    if not baseline_path.exists():
        print(f"[WARN] No baseline file at {baseline_path}. Treating as initial baseline.")
        sys.exit(0)

    m_path = artifacts / "manifest.json"
    k_path = artifacts / "merkle.json"
    if not m_path.exists() or not k_path.exists():
        print("[ERROR] Missing manifest.json or merkle.json in artifacts")
        sys.exit(2)

    manifest = json.loads(m_path.read_text())
    merkle = json.loads(k_path.read_text())

    produced_root = manifest.get("merkle_root")
    if not produced_root or produced_root != merkle.get("root"):
        print("[ERROR] Produced merkle root does not match manifest")
        sys.exit(2)

    baseline = json.loads(baseline_path.read_text())
    baseline_root = baseline.get("merkle_root") or baseline.get("root")

    if not baseline_root:
        print("[ERROR] Baseline missing merkle_root/root")
        sys.exit(2)

    if produced_root != baseline_root:
        if os.environ.get("DRIFT_ACCEPTED", "").lower() in {"1", "true", "yes"}:
            print("[OK] Drift accepted via DRIFT_ACCEPTED env.")
            sys.exit(0)
        print(f"[ERROR] Drift detected. produced={produced_root} baseline={baseline_root}")
        sys.exit(3)

    print("[OK] No drift detected.")


if __name__ == "__main__":
    main()
