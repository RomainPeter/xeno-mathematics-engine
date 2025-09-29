"""
PCAP (Proof-Carrying Action Plan) implementation for event persistence.
Provides PCAPWriter and PCAPSchema for structured proof storage.
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class PCAPSchema:
    """Schema for PCAP (Proof-Carrying Action Plan)."""

    action: str
    context_hash: str
    obligations: List[str] = field(default_factory=list)
    proofs: List[Dict[str, Any]] = field(default_factory=list)
    justification: Dict[str, Any] = field(default_factory=dict)
    created_ts: int = field(default_factory=lambda: int(time.time()))
    sha256: str = ""
    signer: Optional[str] = None
    signature: Optional[str] = None

    def calculate_hash(self) -> str:
        """Calculate SHA256 hash of the PCAP."""
        # Create canonical JSON representation
        data = {
            "action": self.action,
            "context_hash": self.context_hash,
            "obligations": sorted(self.obligations),  # Sort for deterministic ordering
            "proofs": sorted(self.proofs, key=lambda x: json.dumps(x, sort_keys=True)),
            "justification": self.justification,
            "created_ts": self.created_ts,
        }

        # Convert to canonical JSON
        json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))

        # Calculate hash
        self.sha256 = hashlib.sha256(json_str.encode()).hexdigest()
        return self.sha256

    def to_dict(self) -> Dict[str, Any]:
        """Convert PCAP to dictionary."""
        return {
            "action": self.action,
            "context_hash": self.context_hash,
            "obligations": self.obligations,
            "proofs": self.proofs,
            "justification": self.justification,
            "created_ts": self.created_ts,
            "sha256": self.sha256,
            "signer": self.signer,
            "signature": self.signature,
        }

    def to_json(self) -> str:
        """Convert PCAP to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PCAPSchema":
        """Create PCAP from dictionary."""
        pcap = cls(
            action=data["action"],
            context_hash=data["context_hash"],
            obligations=data.get("obligations", []),
            proofs=data.get("proofs", []),
            justification=data.get("justification", {}),
            created_ts=data.get("created_ts", int(time.time())),
            sha256=data.get("sha256", ""),
            signer=data.get("signer"),
            signature=data.get("signature"),
        )
        return pcap

    @classmethod
    def from_json(cls, json_str: str) -> "PCAPSchema":
        """Create PCAP from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def verify_integrity(self) -> bool:
        """Verify the integrity of the PCAP."""
        if not self.sha256:
            return False

        # Recalculate hash
        calculated_hash = self.calculate_hash()
        return calculated_hash == self.sha256

    def add_obligation(self, obligation: str):
        """Add an obligation to the PCAP."""
        if obligation not in self.obligations:
            self.obligations.append(obligation)

    def add_proof(self, proof: Dict[str, Any]):
        """Add a proof to the PCAP."""
        self.proofs.append(proof)

    def set_justification(self, justification: Dict[str, Any]):
        """Set the justification for the PCAP."""
        self.justification = justification

    def get_proof_count(self) -> int:
        """Get number of proofs."""
        return len(self.proofs)

    def get_obligation_count(self) -> int:
        """Get number of obligations."""
        return len(self.obligations)


class PCAPWriter:
    """Writer for PCAP files with structured storage."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.pcap_dir = self.base_dir / "pcap"
        self.pcap_dir.mkdir(parents=True, exist_ok=True)
        self.written_count = 0

    def write_pcap(
        self, pcap: PCAPSchema, step_id: str, action: Optional[str] = None
    ) -> str:
        """Write a PCAP to file."""
        try:
            # Generate filename
            if action:
                filename = f"{step_id}-{action}.json"
            else:
                filename = f"{step_id}-{pcap.action}.json"

            file_path = self.pcap_dir / filename

            # Calculate hash if not set
            if not pcap.sha256:
                pcap.calculate_hash()

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(pcap.to_json())

            self.written_count += 1

            return str(file_path)

        except Exception as e:
            raise RuntimeError(f"Error writing PCAP: {e}")

    def get_pcap_path(self, step_id: str, action: str) -> str:
        """Get the path for a PCAP file."""
        filename = f"{step_id}-{action}.json"
        return str(self.pcap_dir / filename)

    def list_pcaps(self) -> List[str]:
        """List all PCAP files."""
        return [str(f) for f in self.pcap_dir.glob("*.json")]

    def get_pcap_count(self) -> int:
        """Get number of written PCAPs."""
        return self.written_count

    def clear_pcaps(self):
        """Clear all PCAP files."""
        for file_path in self.pcap_dir.glob("*.json"):
            file_path.unlink()
        self.written_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get PCAP writer statistics."""
        return {
            "written": self.written_count,
            "directory": str(self.pcap_dir),
            "files": len(self.list_pcaps()),
        }


class PCAPManager:
    """Manager for PCAP operations with event integration."""

    def __init__(self, base_dir: str, event_bus=None):
        self.writer = PCAPWriter(base_dir)
        self.event_bus = event_bus
        self.pcaps: List[PCAPSchema] = []

    def create_pcap(
        self,
        action: str,
        context_hash: str,
        step_id: str,
        obligations: Optional[List[str]] = None,
        proofs: Optional[List[Dict[str, Any]]] = None,
        justification: Optional[Dict[str, Any]] = None,
    ) -> PCAPSchema:
        """Create a new PCAP."""
        pcap = PCAPSchema(
            action=action,
            context_hash=context_hash,
            obligations=obligations or [],
            proofs=proofs or [],
            justification=justification or {},
        )

        # Calculate hash
        pcap.calculate_hash()

        # Store in memory
        self.pcaps.append(pcap)

        return pcap

    def write_pcap(
        self, pcap: PCAPSchema, step_id: str, action: Optional[str] = None
    ) -> str:
        """Write a PCAP and emit event."""
        try:
            # Write to file
            file_path = self.writer.write_pcap(pcap, step_id, action)

            # Emit PCAP.Emitted event
            if self.event_bus:
                self.event_bus.publish(
                    {
                        "type": "PCAP.Emitted",
                        "payload": {
                            "path": file_path,
                            "hash": pcap.sha256,
                            "size": len(pcap.to_json()),
                            "action": pcap.action,
                            "step_id": step_id,
                        },
                    }
                )

            return file_path

        except Exception as e:
            # Emit incident event
            if self.event_bus:
                self.event_bus.publish(
                    {
                        "type": "Incident",
                        "level": "error",
                        "payload": {
                            "code": "pcap_write_failed",
                            "message": f"Failed to write PCAP: {e}",
                            "detail": {"step_id": step_id, "action": pcap.action},
                        },
                    }
                )
            raise

    def get_pcap(self, step_id: str, action: str) -> Optional[PCAPSchema]:
        """Get a PCAP by step_id and action."""
        for pcap in self.pcaps:
            if pcap.action == action:
                return pcap
        return None

    def list_pcaps(self) -> List[PCAPSchema]:
        """List all PCAPs."""
        return self.pcaps.copy()

    def get_pcap_by_hash(self, sha256: str) -> Optional[PCAPSchema]:
        """Get a PCAP by its hash."""
        for pcap in self.pcaps:
            if pcap.sha256 == sha256:
                return pcap
        return None

    def verify_all_pcaps(self) -> Dict[str, bool]:
        """Verify integrity of all PCAPs."""
        results = {}
        for pcap in self.pcaps:
            results[pcap.sha256] = pcap.verify_integrity()
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get PCAP manager statistics."""
        return {
            "total_pcaps": len(self.pcaps),
            "writer_stats": self.writer.get_stats(),
            "verified": sum(1 for pcap in self.pcaps if pcap.verify_integrity()),
        }


def create_pcap_from_cegis_iteration(
    iteration: int,
    candidate: Dict[str, Any],
    verdict: Dict[str, Any],
    context_hash: str,
) -> PCAPSchema:
    """Create a PCAP from a CEGIS iteration."""
    pcap = PCAPSchema(
        action=f"cegis_iteration_{iteration}",
        context_hash=context_hash,
        obligations=["verify_candidate", "check_compliance", "generate_proofs"],
        proofs=[
            {"type": "candidate_proof", "candidate": candidate, "verdict": verdict}
        ],
        justification={
            "iteration": iteration,
            "timestamp": time.time(),
            "verdict_valid": verdict.get("valid", False),
        },
    )

    pcap.calculate_hash()
    return pcap


def create_pcap_from_ae_concept(
    concept: Dict[str, Any], context_hash: str
) -> PCAPSchema:
    """Create a PCAP from an AE concept."""
    pcap = PCAPSchema(
        action="ae_concept_exploration",
        context_hash=context_hash,
        obligations=["explore_concept", "validate_intent", "check_extent"],
        proofs=[{"type": "concept_proof", "concept": concept}],
        justification={
            "exploration_type": "attribute_exploration",
            "timestamp": time.time(),
            "concept_valid": True,
        },
    )

    pcap.calculate_hash()
    return pcap
