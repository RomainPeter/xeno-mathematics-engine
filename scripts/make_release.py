#!/usr/bin/env python3
import json
import os
import subprocess
import zipfile
from pathlib import Path


def git_tag_or_commit():
    try:
        tag = subprocess.check_output(["git", "describe", "--tags", "--always"], text=True).strip()
        return tag
    except Exception:
        try:
            h = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
            return h
        except Exception:
            return "snapshot"


def add_tree(z, root: Path, arc_prefix: str):
    for p in root.rglob("*"):
        if p.is_file():
            z.write(p, arcname=str(Path(arc_prefix) / p.relative_to(root)))


def main():
    dist = Path("dist")
    dist.mkdir(exist_ok=True)
    tag = git_tag_or_commit()
    out_zip = dist / f"audit_pack_{tag}.zip"

    # Ensure artifacts exist
    os.system("python scripts/audit_pack.py")
    os.system("python scripts/make_logs.py")

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        # Artifacts
        if Path("out/pcap").exists():
            add_tree(z, Path("out/pcap"), "out/pcap")
        if Path("out/audit").exists():
            add_tree(z, Path("out/audit"), "out/audit")
        if Path("out/metrics").exists():
            add_tree(z, Path("out/metrics"), "out/metrics")
        # Docs
        if Path("docs/2pager.md").exists():
            z.write("docs/2pager.md", "docs/2pager.md")
        if Path("LOGS.md").exists():
            z.write("LOGS.md", "LOGS.md")
        if Path("README.md").exists():
            z.write("README.md", "README.md")

    print(json.dumps({"ok": True, "zip": str(out_zip)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
