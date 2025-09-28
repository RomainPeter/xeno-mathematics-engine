"""
Canonicalization utilities for Discovery Engine 2-Cat.
Migrated from proof-engine-for-code.
"""

import hashlib
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass


@dataclass
class CanonicalForm:
    """Canonical form of a state or choreography."""

    hash: str
    representative: Dict[str, Any]
    witnesses: List[Dict[str, Any]]
    timestamp: str


class Canonicalizer:
    """Canonicalization engine for states and choreographies."""

    def __init__(self):
        self.canonical_forms: Dict[str, CanonicalForm] = {}
        self.equivalence_classes: Dict[str, Set[str]] = {}

    def canonicalize_state(self, state: Dict[str, Any]) -> str:
        """Canonicalize a state and return its hash."""
        # Normalize state data
        normalized = self._normalize_state(state)

        # Calculate canonical hash
        canonical_hash = hashlib.sha256(
            json.dumps(normalized, sort_keys=True).encode()
        ).hexdigest()

        # Store canonical form
        if canonical_hash not in self.canonical_forms:
            self.canonical_forms[canonical_hash] = CanonicalForm(
                hash=canonical_hash,
                representative=normalized,
                witnesses=[state],
                timestamp=state.get("timestamp", ""),
            )
        else:
            # Add as witness
            self.canonical_forms[canonical_hash].witnesses.append(state)

        return canonical_hash

    def canonicalize_choreography(self, choreography: Dict[str, Any]) -> str:
        """Canonicalize a choreography and return its hash."""
        # Normalize choreography data
        normalized = self._normalize_choreography(choreography)

        # Calculate canonical hash
        canonical_hash = hashlib.sha256(
            json.dumps(normalized, sort_keys=True).encode()
        ).hexdigest()

        # Store canonical form
        if canonical_hash not in self.canonical_forms:
            self.canonical_forms[canonical_hash] = CanonicalForm(
                hash=canonical_hash,
                representative=normalized,
                witnesses=[choreography],
                timestamp=choreography.get("timestamp", ""),
            )
        else:
            # Add as witness
            self.canonical_forms[canonical_hash].witnesses.append(choreography)

        return canonical_hash

    def _normalize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize state data for canonicalization."""
        normalized = {}

        # Normalize basic fields
        for key in ["id", "timestamp", "type", "status"]:
            if key in state:
                normalized[key] = state[key]

        # Normalize data field
        if "data" in state:
            normalized["data"] = self._normalize_data(state["data"])

        # Normalize metadata
        if "metadata" in state:
            normalized["metadata"] = self._normalize_data(state["metadata"])

        return normalized

    def _normalize_choreography(self, choreography: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize choreography data for canonicalization."""
        normalized = {}

        # Normalize basic fields
        for key in ["id", "timestamp", "type", "status"]:
            if key in choreography:
                normalized[key] = choreography[key]

        # Normalize operations
        if "operations" in choreography:
            normalized["operations"] = sorted(
                choreography["operations"], key=lambda op: op.get("id", "")
            )

        # Normalize conditions
        if "conditions" in choreography:
            normalized["conditions"] = self._normalize_data(choreography["conditions"])

        return normalized

    def _normalize_data(self, data: Any) -> Any:
        """Normalize data for canonicalization."""
        if isinstance(data, dict):
            return {k: self._normalize_data(v) for k, v in sorted(data.items())}
        elif isinstance(data, list):
            return [self._normalize_data(item) for item in data]
        else:
            return data

    def get_canonical_form(self, hash: str) -> Optional[CanonicalForm]:
        """Get canonical form by hash."""
        return self.canonical_forms.get(hash)

    def get_equivalence_class(self, hash: str) -> Set[str]:
        """Get equivalence class for a hash."""
        return self.equivalence_classes.get(hash, set())

    def get_stats(self) -> Dict[str, Any]:
        """Get canonicalization statistics."""
        return {
            "canonical_forms": len(self.canonical_forms),
            "equivalence_classes": len(self.equivalence_classes),
            "total_witnesses": sum(
                len(form.witnesses) for form in self.canonical_forms.values()
            ),
        }
