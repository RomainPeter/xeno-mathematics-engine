from __future__ import annotations

from pefc.capabilities.registry import IncidentCapabilityRegistry


def test_select_execute_returns_planned():
    """Test that select and execute return planned status."""
    reg = IncidentCapabilityRegistry()
    reg.load_from_config(
        {
            "registry": [
                {
                    "id": "ids-synth",
                    "module": "pefc.capabilities.handlers.ids:IDSHandler",
                    "enabled": True,
                }
            ]
        }
    )
    inc = {
        "id": "i1",
        "type": "robustness.fuzz",
        "severity": "medium",
        "context": {"target": "fn"},
    }
    res = reg.execute(inc)
    assert res["status"] == "planned"
    assert res["handler_id"] == "ids-synth"


def test_select_best_handler():
    """Test that select chooses the best handler."""
    reg = IncidentCapabilityRegistry()
    reg.load_from_config(
        {
            "registry": [
                {
                    "id": "hs-tree",
                    "module": "pefc.capabilities.handlers.hstree:HSTreeHandler",
                    "enabled": True,
                },
                {
                    "id": "opa-rego",
                    "module": "pefc.capabilities.handlers.opa:OPAHandler",
                    "enabled": True,
                },
            ]
        }
    )

    # Test security policy violation (both can handle)
    inc = {
        "id": "i1",
        "type": "security.policy.violation",
        "severity": "high",
    }
    handler = reg.select(inc)
    assert handler is not None
    assert handler.meta.id in ["hs-tree", "opa-rego"]

    # Test robustness fuzz (neither can handle)
    inc2 = {
        "id": "i2",
        "type": "robustness.fuzz",
        "severity": "medium",
    }
    handler2 = reg.select(inc2)
    assert handler2 is None


def test_execute_no_capability():
    """Test execute when no capability is available."""
    reg = IncidentCapabilityRegistry()
    reg.load_from_config({"registry": []})  # No handlers

    inc = {
        "id": "i1",
        "type": "unknown.type",
        "severity": "medium",
    }
    res = reg.execute(inc)
    assert res["status"] == "no-capability"
    assert res["incident_type"] == "unknown.type"
    assert "handlers" in res


def test_execute_with_context():
    """Test execute with context parameter."""
    reg = IncidentCapabilityRegistry()
    reg.load_from_config(
        {
            "registry": [
                {
                    "id": "hs-tree",
                    "module": "pefc.capabilities.handlers.hstree:HSTreeHandler",
                    "enabled": True,
                }
            ]
        }
    )

    inc = {
        "id": "i1",
        "type": "security.policy.violation",
        "severity": "medium",
    }
    ctx = {"user": "test", "session": "abc123"}
    res = reg.execute(inc, ctx)
    assert res["status"] == "planned"
    assert res["handler_id"] == "hs-tree"
