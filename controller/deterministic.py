"""Compatibility shim that proxies to proofengine controller module."""

from proofengine.controller import deterministic as _impl

__all__ = getattr(_impl, "__all__", [])


def __getattr__(name):  # pragma: no cover
    return getattr(_impl, name)


def __setattr__(name, value):  # pragma: no cover
    setattr(_impl, name, value)
