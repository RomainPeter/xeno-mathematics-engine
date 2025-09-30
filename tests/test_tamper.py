#!/usr/bin/env python3
"""
Tamper tests for PCAP integrity
Tests that modified PCAPs are rejected by verifier
"""

import json
import tempfile
import os


def test_pcap_tamper_after_attestation():
    """Test that modifying PCAP after attestation is rejected"""
    # Create a valid PCAP
    pcap = {
        "version": "0.1.0",
        "id": "pcap-test-tamper",
        "action": {"name": "test_action", "params": {}, "target": "test_target"},
        "context_hash": "a" * 64,
        "obligations": ["k-1"],
        "justification": {
            "time_ms": 100,
            "audit_cost": 0.1,
            "security_risk": 0.0,
            "info_loss": 0.0,
            "tech_debt": 0.0,
        },
        "proofs": [
            {
                "id": "p-1",
                "type": "unit_test",
                "runner": "pytest",
                "args": ["test_file.py"],
                "expect": "pass",
            }
        ],
        "attestation": {
            "verdict": "accepted",
            "ts": "2025-09-27T12:00:00Z",
            "signature": "test:signature",
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(pcap, f, indent=2)
        pcap_path = f.name

    try:
        # Tamper with the PCAP
        with open(pcap_path, "r") as f:
            tampered_pcap = json.load(f)

        # Modify the action (should invalidate context_hash)
        tampered_pcap["action"]["name"] = "malicious_action"

        with open(pcap_path, "w") as f:
            json.dump(tampered_pcap, f, indent=2)

        # Verify should detect tampering
        from scripts.verifier import verify_pcap_file

        result = verify_pcap_file(pcap_path)

        # Should be rejected due to context_hash mismatch
        assert result["verdict"] == "rejected"
        assert "tamper" in result.get("errors", []) or "context" in result.get("errors", [])

    finally:
        os.unlink(pcap_path)


def test_missing_obligation_failure():
    """Test that missing required proof triggers missing_obligation error"""
    pcap = {
        "version": "0.1.0",
        "id": "pcap-missing-proof",
        "action": {"name": "test_action", "params": {}, "target": "test_target"},
        "context_hash": "b" * 64,
        "obligations": ["k-semver-1", "k-perf-1"],  # Requires 2 proofs
        "justification": {
            "time_ms": 100,
            "audit_cost": 0.1,
            "security_risk": 0.0,
            "info_loss": 0.0,
            "tech_debt": 0.0,
        },
        "proofs": [
            {
                "id": "p-1",
                "type": "unit_test",
                "runner": "pytest",
                "args": ["test_file.py"],
                "expect": "pass",
            }
            # Missing second proof for k-perf-1
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(pcap, f, indent=2)
        pcap_path = f.name

    try:
        from scripts.verifier import verify_pcap_file

        result = verify_pcap_file(pcap_path)

        # Should fail with missing_obligation
        assert result["verdict"] == "rejected"
        assert any("missing_obligation" in str(error) for error in result.get("errors", []))

    finally:
        os.unlink(pcap_path)


def test_budget_exceeded_failure():
    """Test that exceeding time budget triggers budget_exceeded error"""
    pcap = {
        "version": "0.1.0",
        "id": "pcap-budget-exceeded",
        "action": {"name": "slow_action", "params": {}, "target": "test_target"},
        "context_hash": "c" * 64,
        "obligations": [],
        "justification": {
            "time_ms": 60000,  # 60 seconds - exceeds typical budget
            "audit_cost": 0.1,
            "security_risk": 0.0,
            "info_loss": 0.0,
            "tech_debt": 0.0,
        },
        "proofs": [],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(pcap, f, indent=2)
        pcap_path = f.name

    try:
        from scripts.verifier import verify_pcap_file

        result = verify_pcap_file(pcap_path)

        # Should fail with budget_exceeded
        assert result["verdict"] == "rejected"
        assert any("budget_exceeded" in str(error) for error in result.get("errors", []))

    finally:
        os.unlink(pcap_path)


if __name__ == "__main__":
    test_pcap_tamper_after_attestation()
    test_missing_obligation_failure()
    test_budget_exceeded_failure()
    print("All tamper tests passed!")
