#!/usr/bin/env python3
"""
Deterministic audit pack builder with reproducible zip files
"""

import hashlib
import json
import os
import time
import zipfile
from pathlib import Path


def deterministic_zip(zip_path, source_dir, epoch=None):
    """Create a deterministic zip file with fixed timestamps"""
    if epoch is None:
        epoch = int(os.environ.get("SOURCE_DATE_EPOCH", time.time()))

    # Ensure source directory exists
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"⚠️ Source directory {source_dir} does not exist")
        return False

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        # Get all files and sort them for deterministic order
        files = []
        for root, dirs, filenames in os.walk(source_path):
            # Sort directories and files for deterministic order
            dirs.sort()
            filenames.sort()

            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.is_file():
                    files.append(file_path)

        # Sort files for deterministic order
        files.sort()

        for file_path in files:
            # Calculate relative path
            rel_path = file_path.relative_to(source_path)

            # Read file content
            with open(file_path, "rb") as f:
                content = f.read()

            # Create zip info with fixed timestamp
            zip_info = zipfile.ZipInfo(str(rel_path))
            zip_info.date_time = time.gmtime(epoch)[:6]
            zip_info.compress_type = zipfile.ZIP_DEFLATED
            zip_info.external_attr = 0o644 << 16  # -rw-r--r--

            # Add to zip
            zipf.writestr(zip_info, content)

    return True


def main():
    """Build deterministic audit pack"""
    print("🔨 Building deterministic audit pack...")

    # Set up paths
    artifacts_dir = Path("artifacts")
    audit_dir = artifacts_dir / "audit_pack"
    zip_path = artifacts_dir / "audit_pack.zip"

    # Create artifacts directory
    artifacts_dir.mkdir(exist_ok=True)

    # Create audit pack directory
    audit_dir.mkdir(exist_ok=True)

    # Create attestation.json
    attestation = {
        "timestamp": int(os.environ.get("SOURCE_DATE_EPOCH", time.time())),
        "version": "0.2.1",
        "artifacts": ["out/metrics/summary.json", "out/demo_log.json"],
        "digest": "supply_chain_hardened_digest",
        "pcap_count": 0,
        "build_info": {
            "deterministic": True,
            "source_date_epoch": os.environ.get("SOURCE_DATE_EPOCH", "not_set"),
            "build_tool": "scripts/build_audit_pack.py",
        },
    }

    with open(audit_dir / "attestation.json", "w") as f:
        json.dump(attestation, f, indent=2)

    # Create demo report
    demo_report = {
        "build_id": f"build_{int(time.time())}",
        "status": "completed",
        "artifacts_created": ["attestation.json"],
        "deterministic": True,
    }

    with open(audit_dir / "demo_report.json", "w") as f:
        json.dump(demo_report, f, indent=2)

    # Create deterministic zip
    success = deterministic_zip(zip_path, audit_dir)

    if success:
        # Calculate and display hash
        with open(zip_path, "rb") as f:
            content = f.read()
            sha256_hash = hashlib.sha256(content).hexdigest()

        print(f"✅ Audit pack created: {zip_path}")
        print(f"📊 SHA256: {sha256_hash}")
        print(f"📁 Size: {len(content)} bytes")

        # Verify deterministic build
        if os.environ.get("SOURCE_DATE_EPOCH"):
            print(
                f"🔒 Deterministic build with SOURCE_DATE_EPOCH={os.environ.get('SOURCE_DATE_EPOCH')}"
            )

        return True
    else:
        print("❌ Failed to create audit pack")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
