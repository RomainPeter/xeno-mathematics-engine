"""
Tests for provider registry: strict get_provider and listing.
"""

import pytest

from pefc.pack.providers import get_provider, list_providers, register_provider


def test_list_providers_nonempty():
    names = list_providers()
    assert isinstance(names, list)
    assert "noop" in names


def test_get_provider_strict_unknown():
    with pytest.raises(ValueError):
        get_provider("does-not-exist")


def test_register_and_use_provider():
    def _dummy(x):
        return {"x": x}

    name = "dummy_test"
    # Ensure uniqueness across test runs
    if name not in list_providers():
        register_provider(name, _dummy)
    p = get_provider(name)
    out = p(7)
    assert out == {"x": 7}
