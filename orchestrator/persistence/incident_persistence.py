"""
Incident persistence for orchestrator.
Handles incident journaling and persistence.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...pefc.incidents.types import Incident


class IncidentPersistence:
    """Incident persistence manager."""

    def __init__(self, audit_dir: str = "audit"):
        self.audit_dir = Path(audit_dir)
        self.incidents_file = self.audit_dir / "incidents.jsonl"
        self.journal_file = self.audit_dir / "journal.jsonl"

        # Ensure directories exist
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    async def persist_incident(
        self, run_id: str, incident: Incident, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Persist incident to audit directory.

        Args:
            run_id: Run identifier
            incident: Incident to persist
            context: Additional context

        Returns:
            Persistence metadata
        """
        # Create incident data
        incident_data = {
            "id": incident.id,
            "type": incident.type,
            "severity": incident.severity,
            "context": {**incident.context, **(context or {})},
            "evidence_refs": incident.evidence_refs,
            "obligations": incident.obligations,
            "V_target": incident.V_target,
            "timestamp": datetime.now().isoformat(),
            "run_id": run_id,
        }

        # Write incident file
        with open(self.incidents_file, "a") as f:
            f.write(json.dumps(incident_data, ensure_ascii=False) + "\n")

        # Write journal entry
        journal_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "incident_raised",
            "run_id": run_id,
            "incident_id": incident.id,
            "incident_type": incident.type,
            "severity": incident.severity,
            "context": incident.context,
            "obligations_count": len(incident.obligations),
        }

        await self._append_journal_entry(journal_entry)

        return {
            "incident_id": incident.id,
            "file_path": str(self.incidents_file),
            "journal_entry": journal_entry,
        }

    async def load_incidents(self, run_id: str) -> List[Dict[str, Any]]:
        """Load incidents for a run."""
        incidents = []

        if not self.incidents_file.exists():
            return incidents

        with open(self.incidents_file, "r") as f:
            for line in f:
                if line.strip():
                    incident = json.loads(line)
                    if incident.get("run_id") == run_id:
                        incidents.append(incident)

        return sorted(incidents, key=lambda x: x["timestamp"])

    async def load_incidents_by_severity(self, run_id: str, severity: str) -> List[Dict[str, Any]]:
        """Load incidents by severity level."""
        all_incidents = await self.load_incidents(run_id)
        return [inc for inc in all_incidents if inc["severity"] == severity]

    async def load_incidents_by_type(self, run_id: str, incident_type: str) -> List[Dict[str, Any]]:
        """Load incidents by type."""
        all_incidents = await self.load_incidents(run_id)
        return [inc for inc in all_incidents if inc["type"] == incident_type]

    async def get_incident_summary(self, run_id: str) -> Dict[str, Any]:
        """Get incident summary for a run."""
        incidents = await self.load_incidents(run_id)

        if not incidents:
            return {
                "total_incidents": 0,
                "by_severity": {},
                "by_type": {},
                "timeline": [],
            }

        # Count by severity
        by_severity = {}
        for incident in incidents:
            severity = incident["severity"]
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # Count by type
        by_type = {}
        for incident in incidents:
            incident_type = incident["type"]
            by_type[incident_type] = by_type.get(incident_type, 0) + 1

        # Timeline
        timeline = [
            {
                "timestamp": incident["timestamp"],
                "type": incident["type"],
                "severity": incident["severity"],
                "id": incident["id"],
            }
            for incident in incidents
        ]

        return {
            "total_incidents": len(incidents),
            "by_severity": by_severity,
            "by_type": by_type,
            "timeline": timeline,
        }

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
