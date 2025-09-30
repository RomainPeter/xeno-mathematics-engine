#!/usr/bin/env python
import argparse
import json
from pathlib import Path
from pefc.events.manifest import create_audit_manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--audit-dir", required=True)
    args = p.parse_args()

    run_dir = Path(args.audit_dir)
    run_id = run_dir.name
    # Normalize JSON(L) line endings before hashing: rewrite journal.jsonl with '\n'
    j = run_dir / "journal.jsonl"
    if j.exists():
        lines = j.read_text().splitlines()
        j.write_text("\n".join(lines) + ("\n" if lines else ""))

    manifest = create_audit_manifest(run_id=run_id, audit_dir=str(run_dir))
    (run_dir / "manifest.json").write_text(json.dumps(manifest.to_dict(), indent=2))
    print("manifest.merkle_root:", manifest.merkle_root)


if __name__ == "__main__":
    main()
