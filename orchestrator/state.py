"""
State management for Discovery Engine 2-Cat.
Handles cognitive state X, journal J, and caches.
"""

import hashlib
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JournalEntry:
    """Single entry in the append-only journal."""

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
    """Append-only journal with Merkle hashing."""

    def __init__(self):
        self.entries: List[JournalEntry] = []
        self.merkle_root: Optional[str] = None

    def append(self, entry: JournalEntry) -> str:
        """Append entry to journal and calculate Merkle hash."""
        # Calculate Merkle parent (previous entry hash)
        if self.entries:
            entry.merkle_parent = self.entries[-1].merkle_curr
        else:
            entry.merkle_parent = "0" * 64  # Genesis hash

        # Calculate current entry hash
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


@dataclass
class XState:
    """Cognitive state X = {H, E, K, A, J, Σ}."""

    H: List[Dict[str, Any]] = field(default_factory=list)  # Hypotheses
    E: List[Dict[str, Any]] = field(default_factory=list)  # Evidence
    K: List[Dict[str, Any]] = field(default_factory=list)  # Constraints
    A: List[Dict[str, Any]] = field(default_factory=list)  # Artifacts
    J: Journal = field(default_factory=Journal)  # Journal
    Sigma: Dict[str, Any] = field(default_factory=dict)  # Seeds/Environment

    # Caches
    closure_cache: Dict[str, List[str]] = field(default_factory=dict)
    implication_cache: Dict[str, bool] = field(default_factory=dict)

    def add_implication(self, implication: Dict[str, Any]) -> str:
        """Add accepted implication to state."""
        impl_id = f"impl_{len(self.A)}"
        implication["id"] = impl_id
        implication["status"] = "accepted"
        implication["timestamp"] = datetime.now().isoformat()

        # Add to artifacts
        self.A.append(
            {
                "id": impl_id,
                "type": "implication",
                "content": implication,
                "produced_by_journal_id": impl_id,
            }
        )

        # Journal entry
        entry = JournalEntry(
            id=impl_id,
            timestamp=implication["timestamp"],
            operator="AE_accept",
            input_refs=implication.get("premises", []),
            output_refs=[impl_id],
            obligations_checked=implication.get("obligations", []),
            proofs_attached=implication.get("proofs", []),
            costs=implication.get("costs", {}),
        )

        self.J.append(entry)

        # Update closure cache
        premise_key = "|".join(sorted(implication.get("premises", [])))
        if premise_key not in self.closure_cache:
            self.closure_cache[premise_key] = []
        self.closure_cache[premise_key].extend(implication.get("conclusions", []))

        return impl_id

    def add_counterexample(self, counterexample: Dict[str, Any]) -> str:
        """Add counterexample to state and update constraints."""
        cex_id = f"cex_{len(self.A)}"
        counterexample["id"] = cex_id
        counterexample["timestamp"] = datetime.now().isoformat()

        # Add to evidence
        self.E.append(
            {
                "id": cex_id,
                "kind": "counterexample",
                "content": counterexample,
                "timestamp": counterexample["timestamp"],
            }
        )

        # Extract new constraints from counterexample
        new_constraints = self._extract_constraints_from_counterexample(counterexample)
        for constraint in new_constraints:
            self.K.append(
                {
                    "id": f"k_{len(self.K)}",
                    "source": "counterexample",
                    "rule": constraint,
                    "severity": "medium",
                    "tags": ["auto_generated"],
                }
            )

        # Journal entry
        entry = JournalEntry(
            id=cex_id,
            timestamp=counterexample["timestamp"],
            operator="AE_reject",
            input_refs=counterexample.get("violates_premise", []),
            output_refs=[cex_id],
            obligations_checked=new_constraints,
            proofs_attached=counterexample.get("evidence", []),
            costs=counterexample.get("costs", {}),
        )

        self.J.append(entry)

        return cex_id

    def _extract_constraints_from_counterexample(self, counterexample: Dict[str, Any]) -> List[str]:
        """Extract new constraints from counterexample."""
        constraints = []

        # Simple constraint extraction logic
        if counterexample.get("violates_premise"):
            constraints.append("premise_validation_required")

        if counterexample.get("violates_conclusion"):
            constraints.append("conclusion_validation_required")

        # Add domain-specific constraints
        evidence = counterexample.get("evidence", [])
        for ev in evidence:
            if "sensitive" in str(ev).lower():
                constraints.append("sensitive_data_handling_required")
            if "legal" in str(ev).lower():
                constraints.append("legal_basis_required")

        return constraints

    def get_state_hash(self) -> str:
        """Get hash of current state for canonicalization."""
        state_data = {
            "H": self.H,
            "E": self.E,
            "K": self.K,
            "A": self.A,
            "merkle_root": self.J.get_merkle_root(),
        }

        return hashlib.sha256(json.dumps(state_data, sort_keys=True).encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "H": self.H,
            "E": self.E,
            "K": self.K,
            "A": self.A,
            "J": {
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
                    for entry in self.J.entries
                ],
            },
            "Sigma": self.Sigma,
        }
