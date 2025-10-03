"""
Audit Pack builder for orchestrator.
Creates signed audit packs with PCAPs, incidents, and metrics.
"""

import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .incident_persistence import IncidentPersistence
from .pcap_persistence import PCAPPersistence


class AuditPackBuilder:
    """Audit Pack builder for orchestrator results."""

    def __init__(self, audit_dir: str = "audit"):
        self.audit_dir = Path(audit_dir)
        self.pcap_persistence = PCAPPersistence(audit_dir)
        self.incident_persistence = IncidentPersistence(audit_dir)

    async def build_audit_pack(
        self,
        run_id: str,
        metrics: Dict[str, Any],
        signer: Optional[str] = None,
        signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build audit pack for a run.

        Args:
            run_id: Run identifier
            metrics: Run metrics
            signer: Optional signer identifier
            signature: Optional signature

        Returns:
            Audit pack metadata
        """
        # Create audit pack directory
        pack_dir = self.audit_dir / "packs" / run_id
        pack_dir.mkdir(parents=True, exist_ok=True)

        # Collect PCAPs
        pcaps = await self.pcap_persistence.list_pcaps(run_id)

        # Collect incidents
        incidents = await self.incident_persistence.load_incidents(run_id)

        # Collect journal entries
        journal_entries = await self._collect_journal_entries(run_id)

        # Create manifest
        manifest = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "pcaps_count": len(pcaps),
            "incidents_count": len(incidents),
            "journal_entries_count": len(journal_entries),
            "metrics": metrics,
            "signer": signer,
            "signature": signature,
        }

        # Write manifest
        manifest_file = pack_dir / "manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=2)

        # Write PCAPs
        pcaps_file = pack_dir / "pcaps.json"
        with open(pcaps_file, "w") as f:
            json.dump(pcaps, f, indent=2)

        # Write incidents
        incidents_file = pack_dir / "incidents.json"
        with open(incidents_file, "w") as f:
            json.dump(incidents, f, indent=2)

        # Write journal
        journal_file = pack_dir / "journal.jsonl"
        with open(journal_file, "w") as f:
            for entry in journal_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # Write metrics
        metrics_file = pack_dir / "metrics.json"
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)

        # Create ZIP archive
        zip_file = self.audit_dir / "packs" / f"{run_id}.zip"
        await self._create_zip_archive(pack_dir, zip_file)

        # Calculate hashes
        sha256_hash = self._calculate_sha256(zip_file)

        # Create Merkle root
        merkle_root = self._calculate_merkle_root(pack_dir)

        # Update manifest with hashes
        manifest["sha256"] = sha256_hash
        manifest["merkle_root"] = merkle_root
        manifest["zip_file"] = str(zip_file)

        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=2)

        return {
            "run_id": run_id,
            "pack_dir": str(pack_dir),
            "zip_file": str(zip_file),
            "manifest": manifest,
            "sha256": sha256_hash,
            "merkle_root": merkle_root,
        }

    async def _collect_journal_entries(self, run_id: str) -> List[Dict[str, Any]]:
        """Collect all journal entries for a run."""
        entries = []

        # Collect from PCAP persistence
        pcap_entries = await self.pcap_persistence.get_journal_entries(run_id)
        entries.extend(pcap_entries)

        # Collect from incident persistence
        incident_entries = await self.incident_persistence.get_journal_entries(run_id)
        entries.extend(incident_entries)

        # Sort by timestamp
        entries.sort(key=lambda x: x["timestamp"])

        return entries

    async def _create_zip_archive(self, source_dir: Path, zip_file: Path) -> None:
        """Create ZIP archive from directory."""
        with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)

    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _calculate_merkle_root(self, dir_path: Path) -> str:
        """Calculate Merkle root of directory contents."""
        # Collect all file hashes
        file_hashes = []

        for file_path in sorted(dir_path.rglob("*")):
            if file_path.is_file():
                file_hash = self._calculate_sha256(file_path)
                file_hashes.append(file_hash)

        # Build Merkle tree
        if not file_hashes:
            return "0" * 64

        # Simple Merkle root calculation
        while len(file_hashes) > 1:
            next_level = []
            for i in range(0, len(file_hashes), 2):
                if i + 1 < len(file_hashes):
                    combined = file_hashes[i] + file_hashes[i + 1]
                else:
                    combined = file_hashes[i] + file_hashes[i]

                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            file_hashes = next_level

        return file_hashes[0]

    async def verify_audit_pack(self, run_id: str) -> Dict[str, Any]:
        """Verify audit pack integrity."""
        pack_dir = self.audit_dir / "packs" / run_id
        zip_file = self.audit_dir / "packs" / f"{run_id}.zip"

        if not pack_dir.exists() or not zip_file.exists():
            return {"valid": False, "error": "Audit pack not found"}

        # Verify manifest
        manifest_file = pack_dir / "manifest.json"
        if not manifest_file.exists():
            return {"valid": False, "error": "Manifest not found"}

        with open(manifest_file, "r") as f:
            manifest = json.load(f)

        # Verify SHA256
        expected_sha256 = manifest.get("sha256")
        if expected_sha256:
            actual_sha256 = self._calculate_sha256(zip_file)
            if actual_sha256 != expected_sha256:
                return {"valid": False, "error": "SHA256 mismatch"}

        # Verify Merkle root
        expected_merkle = manifest.get("merkle_root")
        if expected_merkle:
            actual_merkle = self._calculate_merkle_root(pack_dir)
            if actual_merkle != expected_merkle:
                return {"valid": False, "error": "Merkle root mismatch"}

        return {
            "valid": True,
            "manifest": manifest,
            "sha256": actual_sha256,
            "merkle_root": actual_merkle,
        }
