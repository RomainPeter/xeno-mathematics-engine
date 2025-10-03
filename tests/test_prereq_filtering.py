from __future__ import annotations

from pefc.capabilities.handlers.opa import OPAHandler
from pefc.capabilities.registry import IncidentCapabilityRegistry


def test_prereq_missing_filters(monkeypatch):
    """Test that missing prerequisites filter handlers."""
    h = OPAHandler()
    monkeypatch.setattr(h, "check_prerequisites", lambda: ["bin:opa"])

    reg = IncidentCapabilityRegistry()
    reg.register(h)
    res = reg.select({"type": "security.policy.violation"})
    assert res is None  # filtered out due to missing prereqs


def test_prereq_available_allows(monkeypatch):
    """Test that available prerequisites allow handlers."""
    h = OPAHandler()
    # Mock check_prerequisites to return empty (all prereqs available)
    monkeypatch.setattr(h, "check_prerequisites", lambda: [])

    reg = IncidentCapabilityRegistry()
    reg.register(h)
    res = reg.select({"type": "security.policy.violation"})
    assert res is not None
    assert res.meta.id == "opa-rego"


def test_multiple_handlers_prereq_filtering(monkeypatch):
    """Test prereq filtering with multiple handlers."""
    reg = IncidentCapabilityRegistry()

    # Register handlers with different prereq status
    h1 = OPAHandler()
    monkeypatch.setattr(h1, "check_prerequisites", lambda: ["bin:opa"])  # missing

    h2 = OPAHandler()
    monkeypatch.setattr(h2, "check_prerequisites", lambda: [])  # available

    reg.register(h1)
    reg.register(h2)

    # Should select the one with available prereqs
    res = reg.select({"type": "security.policy.violation"})
    assert res is not None
    assert res.meta.id == "opa-rego"


def test_no_handlers_available_after_prereq_filter(monkeypatch):
    """Test when no handlers are available after prereq filtering."""
    reg = IncidentCapabilityRegistry()

    h = OPAHandler()
    monkeypatch.setattr(h, "check_prerequisites", lambda: ["bin:opa", "bin:other"])

    reg.register(h)
    res = reg.select({"type": "security.policy.violation"})
    assert res is None


def test_prereq_missing_in_list_handlers(monkeypatch):
    """Test that list_handlers shows missing prerequisites."""
    reg = IncidentCapabilityRegistry()

    h = OPAHandler()
    monkeypatch.setattr(h, "check_prerequisites", lambda: ["bin:opa"])

    reg.register(h)
    lst = reg.list_handlers()
    assert len(lst) == 1
    assert lst[0]["prereq_missing"] == ["bin:opa"]
