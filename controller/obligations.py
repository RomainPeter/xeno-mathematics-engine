"""Compatibility shim that proxies attribute access to proofengine module."""

from proofengine.controller import obligations as _impl

__all__ = getattr(_impl, "__all__", [])


def __getattr__(name):  # pragma: no cover - delegation
    return getattr(_impl, name)


def __setattr__(name, value):  # pragma: no cover - delegation
    setattr(_impl, name, value)
