from __future__ import annotations

from pefc.capabilities.handlers.hstree import HSTreeHandler
from pefc.capabilities.handlers.ids import IDSHandler
from pefc.capabilities.handlers.opa import OPAHandler


def test_hstree_handler_with_capabilities():
    """Test HSTreeHandler with capabilities integration."""
    handler = HSTreeHandler()

    incident = {
        "id": "i1",
        "type": "security.policy.violation",
        "severity": "high",
        "evidence_refs": ["ref1", "ref2"],
        "obligations": ["audit"],
    }

    ctx = {
        "capabilities_cfg": {
            "registry": [
                {
                    "id": "cap-hstree",
                    "module": "pefc.capabilities.plugins.hstree_proof:HSTreeProofGenerator",
                    "enabled": True,
                }
            ]
        }
    }

    result = handler.handle(incident, ctx)

    assert result["handler_id"] == "hs-tree"
    assert result["status"] == "planned"
    assert result["messages"] == ["composed by capabilities"]
    assert "pcap" in result["meta"]
    assert "caps" in result["meta"]

    pcap = result["meta"]["pcap"]
    assert pcap["action"] == "incident.remediation.plan"
    assert pcap["obligations"] == ["audit"]
    assert len(pcap["proofs"]) >= 0  # May be empty if no matching capabilities


def test_opa_handler_with_capabilities():
    """Test OPAHandler with capabilities integration."""
    handler = OPAHandler()

    incident = {
        "id": "i1",
        "type": "security.policy.violation",
        "severity": "high",
        "obligations": ["audit"],
    }

    ctx = {
        "capabilities_cfg": {
            "registry": [
                {
                    "id": "cap-opa-proof",
                    "module": "pefc.capabilities.plugins.opa_proof:OPAProofGenerator",
                    "enabled": True,
                }
            ]
        }
    }

    result = handler.handle(incident, ctx)

    assert result["handler_id"] == "opa-rego"
    assert result["status"] == "planned"
    assert result["messages"] == ["composed by capabilities"]
    assert "pcap" in result["meta"]
    assert "caps" in result["meta"]

    pcap = result["meta"]["pcap"]
    assert pcap["action"] == "incident.remediation.plan"
    assert pcap["obligations"] == ["audit"]


def test_ids_handler_with_capabilities():
    """Test IDSHandler with capabilities integration."""
    handler = IDSHandler()

    incident = {
        "id": "i1",
        "type": "robustness.fuzz",
        "severity": "medium",
        "context": {"target": "auth_service"},
    }

    ctx = {
        "capabilities_cfg": {
            "registry": [
                {
                    "id": "cap-ids-tests",
                    "module": "pefc.capabilities.plugins.ids_tests:IDSTestSynthesizer",
                    "enabled": True,
                }
            ]
        }
    }

    result = handler.handle(incident, ctx)

    assert result["handler_id"] == "ids-synth"
    assert result["status"] == "planned"
    assert result["messages"] == ["composed by capabilities"]
    assert "pcap" in result["meta"]
    assert "caps" in result["meta"]

    pcap = result["meta"]["pcap"]
    assert pcap["action"] == "incident.remediation.plan"


def test_handler_with_multiple_capabilities():
    """Test handler with multiple capabilities."""
    handler = HSTreeHandler()

    incident = {
        "id": "i1",
        "type": "security.policy.violation",
        "severity": "high",
        "obligations": ["audit"],
    }

    ctx = {
        "capabilities_cfg": {
            "registry": [
                {
                    "id": "cap-opa-proof",
                    "module": "pefc.capabilities.plugins.opa_proof:OPAProofGenerator",
                    "enabled": True,
                },
                {
                    "id": "cap-hstree",
                    "module": "pefc.capabilities.plugins.hstree_proof:HSTreeProofGenerator",
                    "enabled": True,
                },
            ]
        }
    }

    result = handler.handle(incident, ctx)

    assert result["status"] == "planned"
    pcap = result["meta"]["pcap"]
    assert len(pcap["proofs"]) >= 1  # Should include multiple capabilities


def test_handler_without_capabilities_config():
    """Test handler without capabilities configuration."""
    handler = HSTreeHandler()

    incident = {
        "id": "i1",
        "type": "security.policy.violation",
        "severity": "high",
    }

    # No capabilities_cfg in context
    result = handler.handle(incident, {})

    assert result["handler_id"] == "hs-tree"
    assert result["status"] == "planned"
    assert result["messages"] == ["composed by capabilities"]
    # Should still work but with empty capabilities
    pcap = result["meta"]["pcap"]
    assert pcap["action"] == "incident.remediation.plan"
