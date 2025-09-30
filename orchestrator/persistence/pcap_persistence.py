"""
PCAP persistence for orchestrator.
Handles Proof-Carrying Action Plan persistence and journaling.
"""

import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ...pefc.pcap.model import PCAP
from ...pefc.pcap.utils import canonical_hash


class PCAPPersistence:
    """PCAP persistence manager."""

    def __init__(self, audit_dir: str = "audit"):
        self.audit_dir = Path(audit_dir)
        self.pcap_dir = self.audit_dir / "pcaps"
        self.journal_file = self.audit_dir / "journal.jsonl"

        # Ensure directories exist
        self.pcap_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    async def persist_pcap(
        self,
        run_id: str,
        pcap: PCAP,
        signer: Optional[str] = None,
        signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Persist PCAP to audit directory.

        Args:
            run_id: Run identifier
            pcap: PCAP to persist
            signer: Optional signer identifier
            signature: Optional signature

        Returns:
            Persistence metadata
        """
        # Generate PCAP ID
        pcap_id = self._generate_pcap_id(pcap)

        # Create PCAP directory for this run
        run_pcap_dir = self.pcap_dir / run_id
        run_pcap_dir.mkdir(exist_ok=True)

        # Serialize PCAP
        pcap_data = {
            "id": pcap_id,
            "action": pcap.action,
            "context_hash": pcap.context_hash,
            "obligations": pcap.obligations,
            "justification": pcap.justification.dict(),
            "proofs": [proof.dict() for proof in pcap.proofs],
            "meta": pcap.meta,
            "timestamp": datetime.now().isoformat(),
            "run_id": run_id,
        }

        # Add signature if provided
        if signer and signature:
            pcap_data["signer"] = signer
            pcap_data["signature"] = signature

        # Write PCAP file
        pcap_file = run_pcap_dir / f"{pcap_id}.json"
        with open(pcap_file, "w") as f:
            json.dump(pcap_data, f, indent=2)

        # Write journal entry
        journal_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "pcap_emitted",
            "run_id": run_id,
            "pcap_id": pcap_id,
            "action": pcap.action,
            "context_hash": pcap.context_hash,
            "obligations_count": len(pcap.obligations),
            "proofs_count": len(pcap.proofs),
            "file_path": str(pcap_file.relative_to(self.audit_dir)),
        }

        await self._append_journal_entry(journal_entry)

        return {
            "pcap_id": pcap_id,
            "file_path": str(pcap_file),
            "journal_entry": journal_entry,
        }

    async def load_pcap(self, run_id: str, pcap_id: str) -> Optional[Dict[str, Any]]:
        """Load PCAP from audit directory."""
        pcap_file = self.pcap_dir / run_id / f"{pcap_id}.json"

        if not pcap_file.exists():
            return None

        with open(pcap_file, "r") as f:
            return json.load(f)

    async def list_pcaps(self, run_id: str) -> List[Dict[str, Any]]:
        """List all PCAPs for a run."""
        run_pcap_dir = self.pcap_dir / run_id

        if not run_pcap_dir.exists():
            return []

        pcaps = []
        for pcap_file in run_pcap_dir.glob("*.json"):
            with open(pcap_file, "r") as f:
                pcap_data = json.load(f)
                pcaps.append(pcap_data)

        return sorted(pcaps, key=lambda x: x["timestamp"])

    async def verify_pcap_integrity(self, run_id: str, pcap_id: str) -> bool:
        """Verify PCAP integrity."""
        pcap_data = await self.load_pcap(run_id, pcap_id)
        if not pcap_data:
            return False

        # Verify context hash
        expected_hash = canonical_hash(
            {
                "action": pcap_data["action"],
                "obligations": pcap_data["obligations"],
                "justification": pcap_data["justification"],
            }
        )

        return pcap_data["context_hash"] == expected_hash

    def _generate_pcap_id(self, pcap: PCAP) -> str:
        """Generate unique PCAP ID."""
        content = f"{pcap.action}_{pcap.context_hash}_{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def _append_journal_entry(self, entry: Dict[str, Any]) -> None:
        """Append entry to journal."""
        with open(self.journal_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    async def get_journal_entries(self, run_id: str) -> List[Dict[str, Any]]:
        """Get journal entries for a run."""
        entries = []

        if not self.journal_file.exists():
            return entries

        with open(self.journal_file, "r") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if entry.get("run_id") == run_id:
                        entries.append(entry)

        return entries
