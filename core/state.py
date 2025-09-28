"""
State management for Discovery Engine 2-Cat.
Core state components migrated from proof-engine-for-code.
"""

import hashlib
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class State:
    """Base state for Discovery Engine operations."""

    id: str
    timestamp: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """Calculate hash of the state."""
        state_data = {
            "id": self.id,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
        }
        return hashlib.sha256(
            json.dumps(state_data, sort_keys=True).encode()
        ).hexdigest()


@dataclass
class CognitiveState:
    """Cognitive state X = {H, E, K, A, J, Σ}."""

    H: List[Dict[str, Any]] = field(default_factory=list)  # Hypotheses
    E: List[Dict[str, Any]] = field(default_factory=list)  # Evidence
    K: List[Dict[str, Any]] = field(default_factory=list)  # Constraints
    A: List[Dict[str, Any]] = field(default_factory=list)  # Artifacts
    J: "Journal" = field(default_factory=lambda: Journal())  # Journal
    Sigma: Dict[str, Any] = field(default_factory=dict)  # Seeds/Environment

    def get_state_hash(self) -> str:
        """Get hash of current cognitive state."""
        state_data = {
            "H": self.H,
            "E": self.E,
            "K": self.K,
            "A": self.A,
            "merkle_root": self.J.get_merkle_root() if self.J else None,
            "Sigma": self.Sigma,
        }
        return hashlib.sha256(
            json.dumps(state_data, sort_keys=True).encode()
        ).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert cognitive state to dictionary."""
        return {
            "H": self.H,
            "E": self.E,
            "K": self.K,
            "A": self.A,
            "J": self.J.to_dict() if self.J else {},
            "Sigma": self.Sigma,
        }


@dataclass
class JournalEntry:
    """Journal entry with Merkle hashing."""

    id: str
    timestamp: str
    operator: str
    input_refs: List[str]
    output_refs: List[str]
    obligations_checked: List[str]
    proofs_attached: List[str]
    costs: Dict[str, float]
    merkle_parent: str
    merkle_curr: str
    signature: Optional[str] = None


class Journal:
    """Journal with Merkle hashing for integrity."""

    def __init__(self):
        self.entries: List[JournalEntry] = []
        self.merkle_root: Optional[str] = None

    def append(self, entry: JournalEntry) -> str:
        """Append entry to journal and calculate Merkle hash."""
        # Calculate Merkle parent
        if self.entries:
            entry.merkle_parent = self.entries[-1].merkle_curr
        else:
            entry.merkle_parent = "0" * 64  # Genesis hash

        # Calculate current hash
        entry_data = {
            "id": entry.id,
            "timestamp": entry.timestamp,
            "operator": entry.operator,
            "input_refs": entry.input_refs,
            "output_refs": entry.output_refs,
            "obligations_checked": entry.obligations_checked,
            "proofs_attached": entry.proofs_attached,
            "costs": entry.costs,
            "merkle_parent": entry.merkle_parent,
        }

        entry.merkle_curr = hashlib.sha256(
            json.dumps(entry_data, sort_keys=True).encode()
        ).hexdigest()

        self.entries.append(entry)
        self._update_merkle_root()

        return entry.merkle_curr

    def _update_merkle_root(self):
        """Update Merkle root from all entries."""
        if not self.entries:
            self.merkle_root = None
            return

        # Simple Merkle tree: hash of all entry hashes
        hashes = [entry.merkle_curr for entry in self.entries]
        combined = "".join(hashes)
        self.merkle_root = hashlib.sha256(combined.encode()).hexdigest()

    def get_merkle_root(self) -> Optional[str]:
        """Get current Merkle root."""
        return self.merkle_root

    def verify_integrity(self) -> bool:
        """Verify journal integrity by recalculating hashes."""
        for i, entry in enumerate(self.entries):
            # Check Merkle parent
            if i == 0:
                expected_parent = "0" * 64
            else:
                expected_parent = self.entries[i - 1].merkle_curr

            if entry.merkle_parent != expected_parent:
                return False

            # Recalculate current hash
            entry_data = {
                "id": entry.id,
                "timestamp": entry.timestamp,
                "operator": entry.operator,
                "input_refs": entry.input_refs,
                "output_refs": entry.output_refs,
                "obligations_checked": entry.obligations_checked,
                "proofs_attached": entry.proofs_attached,
                "costs": entry.costs,
                "merkle_parent": entry.merkle_parent,
            }

            expected_curr = hashlib.sha256(
                json.dumps(entry_data, sort_keys=True).encode()
            ).hexdigest()

            if entry.merkle_curr != expected_curr:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert journal to dictionary."""
        return {
            "version": "0.1.0",
            "entries": [
                {
                    "id": entry.id,
                    "timestamp": entry.timestamp,
                    "operator": entry.operator,
                    "input_refs": entry.input_refs,
                    "output_refs": entry.output_refs,
                    "obligations_checked": entry.obligations_checked,
                    "proofs_attached": entry.proofs_attached,
                    "costs": entry.costs,
                    "merkle_parent": entry.merkle_parent,
                    "merkle_curr": entry.merkle_curr,
                }
                for entry in self.entries
            ],
            "merkle_root": self.merkle_root,
        }
