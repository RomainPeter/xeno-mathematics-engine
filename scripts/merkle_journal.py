"""
Merkle journal utilities for Discovery Engine 2-Cat.
Handles journal integrity, Merkle root calculation, and verification.
"""

import json
import hashlib
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


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


class MerkleJournal:
    """Merkle journal for integrity verification."""

    def __init__(self, journal_file: str = "out/journal.jsonl"):
        self.journal_file = journal_file
        self.entries: List[JournalEntry] = []
        self.merkle_root: Optional[str] = None
        os.makedirs(os.path.dirname(journal_file), exist_ok=True)

    def append_entry(self, entry: JournalEntry) -> str:
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

        # Add to entries
        self.entries.append(entry)

        # Update Merkle root
        self._update_merkle_root()

        # Write to file
        self._write_entry(entry)

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

    def _write_entry(self, entry: JournalEntry):
        """Write entry to journal file."""
        with open(self.journal_file, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

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

    def load_from_file(self):
        """Load entries from journal file."""
        if not os.path.exists(self.journal_file):
            return

        self.entries = []
        with open(self.journal_file, "r") as f:
            for line in f:
                if line.strip():
                    entry_data = json.loads(line)
                    entry = JournalEntry(**entry_data)
                    self.entries.append(entry)

        # Update Merkle root
        self._update_merkle_root()

    def export_summary(self) -> Dict[str, Any]:
        """Export journal summary."""
        return {
            "version": "0.1.0",
            "type": "merkle_journal_summary",
            "merkle_root": self.get_merkle_root(),
            "entry_count": len(self.entries),
            "integrity_verified": self.verify_integrity(),
            "journal_file": self.journal_file,
            "export_timestamp": datetime.now().isoformat(),
        }


def create_ci_entry(workflow_id: str, run_id: str) -> JournalEntry:
    """Create a CI entry for the journal."""
    return JournalEntry(
        id=f"ci_{run_id}",
        timestamp=datetime.now().isoformat(),
        operator="CI_RUN",
        input_refs=["github_workflow", "code_changes"],
        output_refs=["test_results", "artifacts"],
        obligations_checked=["ci_validation", "test_coverage"],
        proofs_attached=["github_actions", "pytest_results"],
        costs={"time_ms": 0, "audit_cost": 0},
        merkle_parent="",  # Will be calculated
        merkle_curr="",  # Will be calculated
    )


def create_ae_entry(implication_id: str, accepted: bool) -> JournalEntry:
    """Create an AE entry for the journal."""
    operator = "AE_accept" if accepted else "AE_reject"
    return JournalEntry(
        id=f"ae_{implication_id}",
        timestamp=datetime.now().isoformat(),
        operator=operator,
        input_refs=[f"implication_{implication_id}"],
        output_refs=[f"result_{implication_id}"],
        obligations_checked=["ae_validation"],
        proofs_attached=["oracle_verification"],
        costs={"time_ms": 100, "audit_cost": 10},
        merkle_parent="",  # Will be calculated
        merkle_curr="",  # Will be calculated
    )


if __name__ == "__main__":
    # Test Merkle journal
    print("Testing Merkle Journal...")

    # Create journal
    journal = MerkleJournal("out/test_journal.jsonl")

    # Add CI entry
    ci_entry = create_ci_entry("CI", "test_run_123")
    ci_hash = journal.append_entry(ci_entry)
    print(f"✅ CI entry added: {ci_hash[:16]}...")

    # Add AE entries
    ae_entry1 = create_ae_entry("impl_1", True)
    ae_hash1 = journal.append_entry(ae_entry1)
    print(f"✅ AE accept entry added: {ae_hash1[:16]}...")

    ae_entry2 = create_ae_entry("impl_2", False)
    ae_hash2 = journal.append_entry(ae_entry2)
    print(f"✅ AE reject entry added: {ae_hash2[:16]}...")

    # Verify integrity
    integrity = journal.verify_integrity()
    print(f"✅ Journal integrity: {integrity}")

    # Export summary
    summary = journal.export_summary()
    print(f"✅ Merkle root: {summary['merkle_root'][:16]}...")
    print(f"✅ Entry count: {summary['entry_count']}")

    print("✅ Merkle journal test completed!")
