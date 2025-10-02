"""
pefc.pack CLI: deterministic pack build/verify.
"""

import argparse
import json
import os
import socket
import uuid
from pathlib import Path

from pefc.events.manifest import AuditManifest, MerkleTree, calculate_file_hash

from .builder import build_pack


def main():
    p = argparse.ArgumentParser(prog="pefc.pack")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build")
    b.add_argument("--config", required=True)
    b.add_argument("--audit-dir", required=True)
    b.add_argument("--seed", type=int, default=0)
    b.add_argument("--no-network", action="store_true")
    b.add_argument("--allow-outside-workspace", action="store_true")

    v = sub.add_parser("verify")
    v.add_argument("--run-dir", required=True)
    # Optionally verify a single file proof from merkle.json
    v.add_argument("--file", required=False, help="Relative path under run dir to verify")

    args = p.parse_args()

    if args.cmd == "build":
        # Hermetic env
        os.environ.setdefault("TZ", "UTC")
        os.environ.setdefault("PYTHONHASHSEED", str(args.seed))
        os.environ.setdefault("SOURCE_DATE_EPOCH", "1700000000")

        if args.no_network:
            try:
                socket.gethostbyname("example.com")
                print("[ERROR] Network egress detected while --no-network is set.")
                raise SystemExit(2)
            except Exception:
                print("[OK] No network egress.")

        run_id = f"r-{uuid.uuid4().hex[:8]}"
        res = build_pack(
            config_path=Path(args.config),
            audit_dir=Path(args.audit_dir),
            run_id=run_id,
            seed=args.seed,
        )
        print(json.dumps(res))
    elif args.cmd == "verify":
        run_dir = Path(args.run_dir)
        manifest_data = json.loads((run_dir / "manifest.json").read_text())
        manifest = AuditManifest.from_dict(manifest_data)
        merkle_ds = json.loads((run_dir / "merkle.json").read_text())

        # 1) Verify manifest integrity by recomputing Merkle root
        ok_manifest = manifest.verify_integrity()

        # 2) Cross-check merkle.json root equals manifest root
        ok_root_match = merkle_ds.get("root") == manifest.merkle_root

        # 3) If --file provided, verify its proof
        file_ok = None
        if args.file:
            try:
                # Find index in order
                order: list[str] = merkle_ds.get("order", [])
                idx = order.index(args.file)
                proofs: list[list[str]] = merkle_ds.get("proofs", [])
                leaves: list[str] = merkle_ds.get("leaves", [])
                # Recompute leaf by recalculating file hash, then hash(hex) like manifest does
                file_hash = calculate_file_hash(str(run_dir / args.file))
                leaf = __import__("hashlib").sha256(file_hash.encode()).hexdigest()
                mt = MerkleTree(leaves)
                file_ok = mt.verify_proof(idx, proofs[idx], leaf)
            except ValueError:
                file_ok = False

        print(
            json.dumps(
                {
                    "ok_manifest": ok_manifest,
                    "ok_root_match": ok_root_match,
                    "file_ok": file_ok,
                }
            )
        )


if __name__ == "__main__":
    main()
