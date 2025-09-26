"""Miscellaneous utility helpers for demo tests."""

from __future__ import annotations


def sanitize_input(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().split())


def add(a: int, b: int) -> int:
    return a + b
