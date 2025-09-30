from __future__ import annotations
from pefc.capabilities.registry import IncidentCapabilityRegistry


def test_load_and_list_basic():
    """Test basic registry loading and listing."""
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
    lst = reg.list_handlers()
    assert any(x["id"] == "hs-tree" for x in lst)


def test_load_multiple_handlers():
    """Test loading multiple handlers."""
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
                {
                    "id": "ids-synth",
                    "module": "pefc.capabilities.handlers.ids:IDSHandler",
                    "enabled": True,
                },
            ]
        }
    )
    lst = reg.list_handlers()
    assert len(lst) == 3
    ids = [h["id"] for h in lst]
    assert "hs-tree" in ids
    assert "opa-rego" in ids
    assert "ids-synth" in ids


def test_list_handlers_metadata():
    """Test that list_handlers returns proper metadata."""
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
    lst = reg.list_handlers()
    assert len(lst) == 1
    handler = lst[0]
    assert "id" in handler
    assert "version" in handler
    assert "provides" in handler
    assert "prereq_missing" in handler
    assert handler["id"] == "hs-tree"
    assert isinstance(handler["provides"], list)
    assert isinstance(handler["prereq_missing"], list)
