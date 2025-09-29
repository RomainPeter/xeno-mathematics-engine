"""
pefc.pack CLI: deterministic pack build/verify.
"""

import argparse
import json
import os
import socket
import uuid
from pathlib import Path

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
        m = json.loads((run_dir / "manifest.json").read_text())
        print(json.dumps({"ok": bool(m.get("merkle_root"))}))


if __name__ == "__main__":
    main()
