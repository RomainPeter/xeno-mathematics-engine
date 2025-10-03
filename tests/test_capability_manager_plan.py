from __future__ import annotations

from pefc.capabilities.manager import CapabilityManager
from pefc.capabilities.plugins.hstree_proof import HSTreeProofGenerator
from pefc.capabilities.plugins.ids_tests import IDSTestSynthesizer
from pefc.capabilities.plugins.opa_proof import OPAProofGenerator


def test_plan_pcap_security_policy_violation():
    """Test PCAP planning for security policy violation."""
    caps = [
        OPAProofGenerator(),
        HSTreeProofGenerator(),
        IDSTestSynthesizer(),
    ]
    manager = CapabilityManager(caps)

    incident = {
        "id": "i1",
        "type": "security.policy.violation",
        "severity": "high",
        "context": {"pattern": "admin_access"},
        "obligations": ["audit", "remediate"],
    }

    pcap = manager.plan_pcap(
        action="incident.remediation.plan",
        incident=incident,
        obligations=incident["obligations"],
    )

    assert pcap.action == "incident.remediation.plan"
    assert pcap.obligations == ["audit", "remediate"]
    assert len(pcap.proofs) >= 2  # Should include OPA and HS-Tree
    assert pcap.context_hash is not None

    # Check that proofs include expected types
    proof_types = [p.type for p in pcap.proofs]
    assert "opa.eval" in proof_types
    assert "hs-tree" in proof_types


def test_plan_pcap_robustness_fuzz():
    """Test PCAP planning for robustness fuzz incident."""
    caps = [
        OPAProofGenerator(),
        HSTreeProofGenerator(),
        IDSTestSynthesizer(),
    ]
    manager = CapabilityManager(caps)

    incident = {
        "id": "i2",
        "type": "robustness.fuzz",
        "severity": "medium",
        "context": {"target": "auth_service"},
    }

    pcap = manager.plan_pcap(
        action="incident.remediation.plan",
        incident=incident,
    )

    assert pcap.action == "incident.remediation.plan"
    assert len(pcap.proofs) >= 1  # Should include IDS tests
    assert pcap.context_hash is not None

    # Check that proofs include IDS tests
    proof_types = [p.type for p in pcap.proofs]
    assert "ids.generate" in proof_types


def test_plan_pcap_context_hash_stable():
    """Test that context hash is stable for same inputs."""
    caps = [OPAProofGenerator()]
    manager = CapabilityManager(caps)

    incident = {
        "id": "i1",
        "type": "security.policy.violation",
        "severity": "high",
    }
    obligations = ["audit"]

    pcap1 = manager.plan_pcap(
        action="test.action",
        incident=incident,
        obligations=obligations,
    )
    pcap2 = manager.plan_pcap(
        action="test.action",
        incident=incident,
        obligations=obligations,
    )

    assert pcap1.context_hash == pcap2.context_hash


def test_plan_pcap_justification_aggregation():
    """Test that V justification is aggregated from capabilities."""
    caps = [
        OPAProofGenerator(),
        HSTreeProofGenerator(),
    ]
    manager = CapabilityManager(caps)

    incident = {
        "id": "i1",
        "type": "security.policy.violation",
        "severity": "high",
    }

    pcap = manager.plan_pcap(
        action="incident.remediation.plan",
        incident=incident,
    )

    # Should aggregate costs from both capabilities
    assert pcap.justification.audit_cost is not None
    assert pcap.justification.time is not None
    assert pcap.justification.audit_cost > 0
    assert pcap.justification.time > 0


def test_plan_pcap_meta_capabilities():
    """Test that PCAP meta includes capability IDs."""
    caps = [
        OPAProofGenerator(),
        HSTreeProofGenerator(),
    ]
    manager = CapabilityManager(caps)

    incident = {
        "id": "i1",
        "type": "security.policy.violation",
        "severity": "high",
    }

    pcap = manager.plan_pcap(
        action="incident.remediation.plan",
        incident=incident,
    )

    assert "capabilities" in pcap.meta
    capability_ids = pcap.meta["capabilities"]
    assert "cap-opa-proof" in capability_ids
    assert "cap-hstree" in capability_ids


def test_plan_pcap_no_matching_capabilities():
    """Test PCAP planning when no capabilities match."""
    caps = [IDSTestSynthesizer()]  # Only handles robustness/regression
    manager = CapabilityManager(caps)

    incident = {
        "id": "i1",
        "type": "security.policy.violation",  # IDS can't handle this
        "severity": "high",
    }

    pcap = manager.plan_pcap(
        action="incident.remediation.plan",
        incident=incident,
    )

    assert pcap.action == "incident.remediation.plan"
    assert len(pcap.proofs) == 0  # No matching capabilities
    assert pcap.meta["capabilities"] == []
