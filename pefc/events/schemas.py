"""
Event schemas for structured event publishing.
Defines event structure v1 with correlation IDs and structured payloads.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class EventSchema:
    """Structured event schema v1."""

    # Core identifiers
    ts: float
    trace_id: str
    run_id: str
    step_id: str

    # Event classification
    phase: str  # "ae" | "cegis" | "orchestrator"
    type: str  # Event type (e.g., "started", "completed", "failed")

    # Payload
    payload: Dict[str, Any] = field(default_factory=dict)

    # Timing information
    timings: Dict[str, float] = field(default_factory=dict)

    # Event metadata
    level: str = "info"  # "debug" | "info" | "warning" | "error" | "critical"
    version: str = "1.0"

    # Correlation
    parent_step_id: Optional[str] = None
    correlation_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ts": self.ts,
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "step_id": self.step_id,
            "phase": self.phase,
            "type": self.type,
            "payload": self.payload,
            "timings": self.timings,
            "level": self.level,
            "version": self.version,
            "parent_step_id": self.parent_step_id,
            "correlation_data": self.correlation_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventSchema":
        """Create from dictionary."""
        return cls(
            ts=data["ts"],
            trace_id=data["trace_id"],
            run_id=data["run_id"],
            step_id=data["step_id"],
            phase=data["phase"],
            type=data["type"],
            payload=data.get("payload", {}),
            timings=data.get("timings", {}),
            level=data.get("level", "info"),
            version=data.get("version", "1.0"),
            parent_step_id=data.get("parent_step_id"),
            correlation_data=data.get("correlation_data", {}),
        )


# Event type constants
class EventTypes:
    """Event type constants for orchestrator."""

    # Orchestrator events
    ORCHESTRATOR_STARTED = "orchestrator.started"
    ORCHESTRATOR_COMPLETED = "orchestrator.completed"
    ORCHESTRATOR_FAILED = "orchestrator.failed"

    # AE events
    AE_STARTED = "ae.started"
    AE_STEP = "ae.step"
    AE_COMPLETED = "ae.completed"
    AE_FAILED = "ae.failed"
    AE_TIMEOUT = "ae.timeout"

    # CEGIS events
    CEGIS_STARTED = "cegis.started"
    CEGIS_STEP = "cegis.step"
    CEGIS_PROPOSED = "cegis.proposed"
    CEGIS_VERIFIED = "cegis.verified"
    CEGIS_REFINED = "cegis.refined"
    CEGIS_COMPLETED = "cegis.completed"
    CEGIS_FAILED = "cegis.failed"
    CEGIS_TIMEOUT = "cegis.timeout"

    # Verification events
    VERIFY_ATTEMPT = "verify.attempt"
    VERIFY_SUCCESS = "verify.success"
    VERIFY_FAILED = "verify.failed"
    VERIFY_TIMEOUT = "verify.timeout"

    # Incident events
    INCIDENT_RAISED = "incident.raised"
    INCIDENT_RESOLVED = "incident.resolved"

    # Budget events
    BUDGET_OVERRUN = "budget.overrun"
    BUDGET_WARNING = "budget.warning"

    # PCAP events
    PCAP_EMITTED = "pcap.emitted"
    PCAP_SIGNED = "pcap.signed"

    # Metrics events
    METRICS_COLLECTED = "metrics.collected"
    METRICS_SUMMARY = "metrics.summary"


class EventBuilder:
    """Builder for structured events."""

    def __init__(self, trace_id: str, run_id: str):
        self.trace_id = trace_id
        self.run_id = run_id
        self.step_counter = 0

    def create_event(
        self,
        phase: str,
        event_type: str,
        payload: Dict[str, Any] = None,
        timings: Dict[str, float] = None,
        level: str = "info",
        parent_step_id: str = None,
    ) -> EventSchema:
        """Create a structured event."""
        self.step_counter += 1
        step_id = f"step_{self.step_counter:06d}"

        return EventSchema(
            ts=datetime.now().timestamp(),
            trace_id=self.trace_id,
            run_id=self.run_id,
            step_id=step_id,
            phase=phase,
            type=event_type,
            payload=payload or {},
            timings=timings or {},
            level=level,
            parent_step_id=parent_step_id,
        )

    def create_ae_event(
        self,
        event_type: str,
        payload: Dict[str, Any] = None,
        timings: Dict[str, float] = None,
        level: str = "info",
    ) -> EventSchema:
        """Create AE-specific event."""
        return self.create_event("ae", event_type, payload, timings, level)

    def create_cegis_event(
        self,
        event_type: str,
        payload: Dict[str, Any] = None,
        timings: Dict[str, float] = None,
        level: str = "info",
    ) -> EventSchema:
        """Create CEGIS-specific event."""
        return self.create_event("cegis", event_type, payload, timings, level)

    def create_orchestrator_event(
        self,
        event_type: str,
        payload: Dict[str, Any] = None,
        timings: Dict[str, float] = None,
        level: str = "info",
    ) -> EventSchema:
        """Create orchestrator-specific event."""
        return self.create_event("orchestrator", event_type, payload, timings, level)
