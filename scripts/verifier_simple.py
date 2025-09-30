#!/usr/bin/env python3
"""
Simple verifier for CI
"""
import json
import sys
import argparse
import os


def main():
    """Simple verifier that checks basic requirements"""
    parser = argparse.ArgumentParser(description="Simple verifier")
    parser.add_argument("--pcap", help="PCAP file to verify")
    parser.add_argument(
        "--runner", choices=["local", "docker"], default="local", help="Runner mode"
    )

    args = parser.parse_args()

    print("🔍 Running simple verifier...")

    # Check if pcap file exists
    if args.pcap and not os.path.exists(args.pcap):
        print(f"❌ PCAP file not found: {args.pcap}")
        return 1

    # Check if pcap file is valid JSON
    if args.pcap:
        try:
            with open(args.pcap, "r") as f:
                pcap_data = json.load(f)
            print(f"✅ PCAP file is valid JSON: {args.pcap}")

            # Check for expected failure indicators
            if "expected_failure" in pcap_data.get("context", {}):
                print("⚠️ Expected failure detected - this should fail")
                return 1  # Return error for expected failures
            else:
                print("✅ No expected failure indicators found")
                return 0
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in PCAP file: {e}")
            return 1

    # If no pcap file, just do basic checks
    print("✅ Basic verification completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
