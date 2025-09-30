#!/usr/bin/env python
import argparse
import json
from pathlib import Path


def fail(msg: str):
    print("[FAIL]", msg)
    raise SystemExit(1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", required=True)
    p.add_argument("--kpi-threshold", type=float, default=0.6)
    p.add_argument("--require-no-fatal", action="store_true")
    args = p.parse_args()

    run_dir = Path(args.run_dir)
    metrics_path = run_dir / "metrics.json"
    journal_path = run_dir / "journal.jsonl"
    manifest_path = run_dir / "manifest.json"

    if not metrics_path.exists():
        fail("metrics.json missing")
    if not journal_path.exists():
        fail("journal.jsonl missing")
    if not manifest_path.exists():
        fail("manifest.json missing; run build_manifest.py first")

    metrics = json.loads(metrics_path.read_text())
    par = metrics.get("cegis", {}).get("patch_accept_rate", 0.0)
    if par < args.kpi_threshold:
        fail(f"patch_accept_rate {par:.3f} < threshold {args.kpi_threshold}")

    # incidents fatal?
    if args.require_no_fatal:
        incidents = metrics.get("global", {}).get("incidents_count", {})
        fatals = sum(v for k, v in incidents.items() if "fatal" in k)
        if fatals > 0:
            fail(f"fatal incidents present: {incidents}")

    # Merkle root drift presence
    manifest = json.loads(manifest_path.read_text())
    if not manifest.get("merkle_root"):
        fail("empty merkle_root")

    print("[OK] E2E checks passed")


if __name__ == "__main__":
    main()
