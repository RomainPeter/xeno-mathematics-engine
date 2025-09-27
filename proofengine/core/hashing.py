"""Hashing helpers for ProofEngine core structures."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .schemas import PCAP, XState


def _stable_dump(payload: Any) -> str:
    """Serialise payload into a deterministic JSON string."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def hash_state(state: XState) -> str:
    """Compute a SHA256 hash for the provided state."""

    payload = state.to_dict()
    payload.pop("state_hash", None)
    return hashlib.sha256(_stable_dump(payload).encode("utf-8")).hexdigest()


def hash_pcap(pcap: PCAP) -> str:
    """Compute a SHA256 hash for a PCAP entry."""

    payload = pcap.to_dict()
    return hashlib.sha256(_stable_dump(payload).encode("utf-8")).hexdigest()


def verify_state_integrity(state: XState) -> bool:
    """Return True if the state's stored hash matches its content."""

    if not state.state_hash:
        return False
    return state.state_hash == hash_state(state)
