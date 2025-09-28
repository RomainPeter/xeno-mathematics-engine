from __future__ import annotations
from pefc.capabilities.loader import build_capabilities


def test_build_capabilities_basic():
    """Test basic capability loading."""
    cfg = {
        "registry": [
            {
                "id": "cap-opa-proof",
                "module": "pefc.capabilities.plugins.opa_proof:OPAProofGenerator",
                "enabled": True,
            }
        ]
    }
    caps = build_capabilities(cfg)
    assert len(caps) == 1
    assert caps[0].meta.id == "cap-opa-proof"


def test_build_capabilities_multiple():
    """Test loading multiple capabilities."""
    cfg = {
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
            {
                "id": "cap-ids-tests",
                "module": "pefc.capabilities.plugins.ids_tests:IDSTestSynthesizer",
                "enabled": True,
            },
        ]
    }
    caps = build_capabilities(cfg)
    assert len(caps) == 3
    ids = [c.meta.id for c in caps]
    assert "cap-opa-proof" in ids
    assert "cap-hstree" in ids
    assert "cap-ids-tests" in ids


def test_build_capabilities_allowlist():
    """Test allowlist filtering."""
    cfg = {
        "allowlist": ["cap-opa-proof"],
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
        ],
    }
    caps = build_capabilities(cfg)
    assert len(caps) == 1
    assert caps[0].meta.id == "cap-opa-proof"


def test_build_capabilities_denylist():
    """Test denylist filtering."""
    cfg = {
        "denylist": ["cap-hstree"],
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
        ],
    }
    caps = build_capabilities(cfg)
    assert len(caps) == 1
    assert caps[0].meta.id == "cap-opa-proof"


def test_build_capabilities_disabled():
    """Test disabled capabilities are skipped."""
    cfg = {
        "registry": [
            {
                "id": "cap-opa-proof",
                "module": "pefc.capabilities.plugins.opa_proof:OPAProofGenerator",
                "enabled": True,
            },
            {
                "id": "cap-hstree",
                "module": "pefc.capabilities.plugins.hstree_proof:HSTreeProofGenerator",
                "enabled": False,
            },
        ]
    }
    caps = build_capabilities(cfg)
    assert len(caps) == 1
    assert caps[0].meta.id == "cap-opa-proof"


def test_build_capabilities_with_params():
    """Test capabilities with parameters."""
    cfg = {
        "registry": [
            {
                "id": "cap-opa-proof",
                "module": "pefc.capabilities.plugins.opa_proof:OPAProofGenerator",
                "enabled": True,
                "params": {
                    "policy_dir": "custom/policies",
                    "query": "data.custom.allow",
                },
            }
        ]
    }
    caps = build_capabilities(cfg)
    assert len(caps) == 1
    cap = caps[0]
    assert cap.policy_dir == "custom/policies"
    assert cap.query == "data.custom.allow"
