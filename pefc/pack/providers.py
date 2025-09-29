"""
Provider registry for metrics/pack-related providers.

Exposes a strict `get_provider(name)` that raises ValueError if unknown,
and `list_providers()` to enumerate valid provider names.
"""

from __future__ import annotations

from typing import Callable, Dict, List


class _Provider:
    def __init__(self, name: str, handler: Callable):
        self.name = name
        self.handler = handler

    def __call__(self, *args, **kwargs):
        return self.handler(*args, **kwargs)


def _noop_provider(*args, **kwargs):
    return {"ok": True, "detail": "noop"}


_REGISTRY: Dict[str, _Provider] = {
    "noop": _Provider("noop", _noop_provider),
}


def list_providers() -> List[str]:
    return sorted(_REGISTRY.keys())


def get_provider(name: str) -> _Provider:
    if name not in _REGISTRY:
        valid = ", ".join(list_providers())
        raise ValueError(f"Unknown provider '{name}'. Valid providers: {valid}")
    return _REGISTRY[name]


def register_provider(name: str, handler: Callable) -> None:
    if not name or not isinstance(name, str):
        raise ValueError("Provider name must be a non-empty string")
    if name in _REGISTRY:
        raise ValueError(f"Provider '{name}' already registered")
    _REGISTRY[name] = _Provider(name, handler)
