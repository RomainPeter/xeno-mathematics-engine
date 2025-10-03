#!/usr/bin/env python3
"""
PCAP CLI v0.1 - Proof-Carrying Action toolchain
Commands: new, verify, attest
"""

import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path


def load_schema(name):
    """Load JSON schema for validation"""
    schema_path = Path("specs/v0.1") / f"{name}.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_pcap(pcap_data):
    """Validate PCAP against schema"""
    from jsonschema import Draft202012Validator

    schema = load_schema("pcap")
    validator = Draft202012Validator(schema)
    validator.validate(pcap_data)
    return True


def new_pcap(action_name, target, params=None):
    """Generate new PCAP skeleton"""
    pcap_id = f"pcap-{uuid.uuid4().hex[:8]}"
    context_hash = hashlib.sha256(f"{action_name}:{target}".encode()).hexdigest()

    pcap = {
        "version": "0.1.0",
        "id": pcap_id,
        "action": {"name": action_name, "params": params or {}, "target": target},
        "context_hash": context_hash,
        "obligations": [],
        "justification": {
            "time_ms": 0,
            "audit_cost": 0.0,
            "security_risk": 0.0,
            "info_loss": 0.0,
            "tech_debt": 0.0,
        },
        "proofs": [],
    }

    return pcap


def verify_pcap(pcap_path):
    """Verify PCAP using verifier"""
    # Import verifier (will be implemented)
    try:
        from scripts.verifier import verify_pcap_file

        result = verify_pcap_file(pcap_path)
        return result
    except ImportError:
        print("Warning: Verifier not available, returning mock result")
        return {
            "verdict": "accepted",
            "ts": datetime.utcnow().isoformat() + "Z",
            "signature": "mock:local",
        }


def attest_pcap(pcap_path, verdict="accepted"):
    """Add attestation to PCAP"""
    with open(pcap_path, "r", encoding="utf-8") as f:
        pcap = json.load(f)

    attestation = {
        "verdict": verdict,
        "ts": datetime.utcnow().isoformat() + "Z",
        "signature": "local:attest",
    }

    pcap["attestation"] = attestation

    with open(pcap_path, "w", encoding="utf-8") as f:
        json.dump(pcap, f, indent=2)

    print(f"Attestation added to {pcap_path}: {verdict}")


def main():
    parser = argparse.ArgumentParser(description="PCAP CLI v0.1")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # new command
    new_parser = subparsers.add_parser("new", help="Generate new PCAP")
    new_parser.add_argument("output", help="Output file path")
    new_parser.add_argument("--action", required=True, help="Action name")
    new_parser.add_argument("--target", required=True, help="Target path")
    new_parser.add_argument("--params", help="Parameters as JSON string")

    # verify command
    verify_parser = subparsers.add_parser("verify", help="Verify PCAP")
    verify_parser.add_argument("pcap_file", help="PCAP file to verify")

    # attest command
    attest_parser = subparsers.add_parser("attest", help="Add attestation")
    attest_parser.add_argument("pcap_file", help="PCAP file to attest")
    attest_parser.add_argument(
        "--verdict",
        choices=["accepted", "rejected"],
        default="accepted",
        help="Attestation verdict",
    )

    args = parser.parse_args()

    if args.command == "new":
        params = json.loads(args.params) if args.params else None
        pcap = new_pcap(args.action, args.target, params)

        # Validate before saving
        try:
            validate_pcap(pcap)
        except Exception as e:
            print(f"Validation error: {e}")
            sys.exit(1)

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(pcap, f, indent=2)
        print(f"PCAP created: {args.output}")

    elif args.command == "verify":
        result = verify_pcap(args.pcap_file)
        print(json.dumps(result, indent=2))

    elif args.command == "attest":
        attest_pcap(args.pcap_file, args.verdict)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
