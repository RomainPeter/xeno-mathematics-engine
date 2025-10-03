#!/usr/bin/env python3
"""
Simple audit pack script for CI
"""

import json
import os
import time
import zipfile


def main():
    """Create simple audit pack"""
    print("📦 Creating simple audit pack...")

    # Create artifacts directory
    os.makedirs("artifacts", exist_ok=True)

    # Create simple attestation
    attestation = {
        "timestamp": time.time(),
        "version": "0.1.0",
        "artifacts": ["out/metrics/summary.json", "out/demo_log.json"],
        "digest": "simple_demo_digest",
        "pcap_count": 0,
    }

    with open("artifacts/attestation.json", "w") as f:
        json.dump(attestation, f, indent=2)

    # Create simple audit pack zip
    zip_path = "artifacts/audit_pack_simple.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        # Add attestation
        zipf.write("artifacts/attestation.json", "attestation.json")

        # Add any existing files
        for file_path in ["out/metrics/summary.json", "out/demo_log.json"]:
            if os.path.exists(file_path):
                zipf.write(file_path, os.path.basename(file_path))

    print(f"✅ Audit pack created: {zip_path}")
    print(f"📊 Attestation: {attestation}")


if __name__ == "__main__":
    main()
