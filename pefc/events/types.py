"""
Event types and schemas for structured telemetry.
Defines Event v1 specification with all required fields and types.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import time
import uuid


class EventLevel(Enum):
    """Event severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class EventType(Enum):
    """Event types for structured telemetry."""

    # Orchestrator events
    ORCHESTRATOR_START = "Orchestrator.Start"
    ORCHESTRATOR_END = "Orchestrator.End"

    # AE (Attribute Exploration) events
    AE_STEP = "AE.Step"
    AE_CONCEPT_EMITTED = "AE.Concept.Emitted"

    # CEGIS events
    CEGIS_ITER_START = "CEGIS.Iter.Start"
    CEGIS_ITER_END = "CEGIS.Iter.End"
    CEGIS_ITER_REFINE = "CEGIS.Iter.Refine"
    CEGIS_ITER_CONVERGED = "CEGIS.Iter.Converged"

    # Verification events
    VERIFY_ATTEMPT = "Verify.Attempt"
    VERIFY_RESULT = "Verify.Result"

    # Budget events
    BUDGET_OVERRUN = "Budget.Overrun"

    # Incident events
    INCIDENT = "Incident"

    # PCAP events
    PCAP_EMITTED = "PCAP.Emitted"

    # Metrics events
    METRICS_SNAPSHOT = "Metrics.Snapshot"


@dataclass
class Timings:
    """Event timing information."""

    start_ns: Optional[int] = None
    end_ns: Optional[int] = None
    dur_ms: Optional[float] = None

    def __post_init__(self):
        if self.start_ns and self.end_ns and self.dur_ms is None:
            self.dur_ms = (self.end_ns - self.start_ns) / 1_000_000


@dataclass
class Event:
    """Base event structure following Event v1 specification."""

    version: str = "1"
    ts: int = field(default_factory=lambda: int(time.time_ns()))
    level: EventLevel = EventLevel.INFO
    trace_id: str = field(default_factory=lambda: f"t-{uuid.uuid4().hex[:16]}")
    run_id: str = field(default_factory=lambda: f"r-{uuid.uuid4().hex[:16]}")
    step_id: str = field(default_factory=lambda: f"s-{uuid.uuid4().hex[:16]}")
    phase: str = "Unknown"
    type: EventType = EventType.ORCHESTRATOR_START
    payload: Dict[str, Any] = field(default_factory=dict)
    timings: Timings = field(default_factory=Timings)
    seq: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "ts": self.ts,
            "level": self.level.value,
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "step_id": self.step_id,
            "phase": self.phase,
            "type": self.type.value,
            "payload": self.payload,
            "timings": {
                "start_ns": self.timings.start_ns,
                "end_ns": self.timings.end_ns,
                "dur_ms": self.timings.dur_ms,
            },
            "seq": self.seq,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        timings_data = data.get("timings", {})
        timings = Timings(
            start_ns=timings_data.get("start_ns"),
            end_ns=timings_data.get("end_ns"),
            dur_ms=timings_data.get("dur_ms"),
        )

        return cls(
            version=data.get("version", "1"),
            ts=data["ts"],
            level=EventLevel(data["level"]),
            trace_id=data["trace_id"],
            run_id=data["run_id"],
            step_id=data["step_id"],
            phase=data["phase"],
            type=EventType(data["type"]),
            payload=data["payload"],
            timings=timings,
            seq=data["seq"],
        )


@dataclass
class OrchestratorEvent(Event):
    """Orchestrator-specific events."""

    def __post_init__(self):
        self.phase = "Orchestrator"
        if self.type == EventType.ORCHESTRATOR_START:
            self.level = EventLevel.INFO
        elif self.type == EventType.ORCHESTRATOR_END:
            self.level = EventLevel.INFO


@dataclass
class AEEvent(Event):
    """Attribute Exploration events."""

    def __post_init__(self):
        self.phase = "AE"
        if self.type == EventType.AE_STEP:
            self.level = EventLevel.INFO
        elif self.type == EventType.AE_CONCEPT_EMITTED:
            self.level = EventLevel.INFO


@dataclass
class CEGISEvent(Event):
    """CEGIS events."""

    def __post_init__(self):
        self.phase = "CEGIS"
        if self.type in [EventType.CEGIS_ITER_START, EventType.CEGIS_ITER_END]:
            self.level = EventLevel.INFO
        elif self.type == EventType.CEGIS_ITER_REFINE:
            self.level = EventLevel.INFO
        elif self.type == EventType.CEGIS_ITER_CONVERGED:
            self.level = EventLevel.INFO


@dataclass
class VerifyEvent(Event):
    """Verification events."""

    def __post_init__(self):
        self.phase = "Verify"
        if self.type == EventType.VERIFY_ATTEMPT:
            self.level = EventLevel.INFO
        elif self.type == EventType.VERIFY_RESULT:
            self.level = EventLevel.INFO


@dataclass
class BudgetEvent(Event):
    """Budget overrun events."""

    def __post_init__(self):
        self.phase = "Budget"
        if self.type == EventType.BUDGET_OVERRUN:
            self.level = EventLevel.WARN


@dataclass
class IncidentEvent(Event):
    """Incident events."""

    def __post_init__(self):
        self.phase = "Incident"
        self.level = EventLevel.ERROR

        # Ensure incident payload has required fields
        if "code" not in self.payload:
            self.payload["code"] = "unknown"
        if "message" not in self.payload:
            self.payload["message"] = "Unknown incident"
        if "detail" not in self.payload:
            self.payload["detail"] = {}


@dataclass
class PCAPEvent(Event):
    """PCAP emission events."""

    def __post_init__(self):
        self.phase = "PCAP"
        self.level = EventLevel.INFO

        # Ensure PCAP payload has required fields
        if "path" not in self.payload:
            self.payload["path"] = ""
        if "hash" not in self.payload:
            self.payload["hash"] = ""
        if "size" not in self.payload:
            self.payload["size"] = 0


@dataclass
class MetricsEvent(Event):
    """Metrics snapshot events."""

    def __post_init__(self):
        self.phase = "Metrics"
        self.level = EventLevel.INFO


def create_event(
    event_type: EventType,
    payload: Dict[str, Any],
    trace_id: Optional[str] = None,
    run_id: Optional[str] = None,
    step_id: Optional[str] = None,
    level: EventLevel = EventLevel.INFO,
    phase: Optional[str] = None,
) -> Event:
    """Create a new event with specified parameters."""
    event = Event(
        level=level,
        trace_id=trace_id or f"t-{uuid.uuid4().hex[:16]}",
        run_id=run_id or f"r-{uuid.uuid4().hex[:16]}",
        step_id=step_id or f"s-{uuid.uuid4().hex[:16]}",
        type=event_type,
        payload=payload,
    )

    if phase:
        event.phase = phase

    return event


def create_orchestrator_start_event(
    run_id: str, trace_id: str, payload: Dict[str, Any]
) -> OrchestratorEvent:
    """Create Orchestrator.Start event."""
    event = OrchestratorEvent(
        trace_id=trace_id,
        run_id=run_id,
        type=EventType.ORCHESTRATOR_START,
        payload=payload,
    )
    return event


def create_orchestrator_end_event(
    run_id: str, trace_id: str, payload: Dict[str, Any]
) -> OrchestratorEvent:
    """Create Orchestrator.End event."""
    event = OrchestratorEvent(
        trace_id=trace_id,
        run_id=run_id,
        type=EventType.ORCHESTRATOR_END,
        payload=payload,
    )
    return event


def create_ae_step_event(
    run_id: str, trace_id: str, step_id: str, payload: Dict[str, Any]
) -> AEEvent:
    """Create AE.Step event."""
    event = AEEvent(
        trace_id=trace_id,
        run_id=run_id,
        step_id=step_id,
        type=EventType.AE_STEP,
        payload=payload,
    )
    return event


def create_ae_concept_emitted_event(
    run_id: str, trace_id: str, step_id: str, payload: Dict[str, Any]
) -> AEEvent:
    """Create AE.Concept.Emitted event."""
    event = AEEvent(
        trace_id=trace_id,
        run_id=run_id,
        step_id=step_id,
        type=EventType.AE_CONCEPT_EMITTED,
        payload=payload,
    )
    return event


def create_cegis_iter_start_event(
    run_id: str, trace_id: str, step_id: str, iteration: int, payload: Dict[str, Any]
) -> CEGISEvent:
    """Create CEGIS.Iter.Start event."""
    event = CEGISEvent(
        trace_id=trace_id,
        run_id=run_id,
        step_id=step_id,
        type=EventType.CEGIS_ITER_START,
        payload={**payload, "iteration": iteration},
    )
    return event


def create_cegis_iter_end_event(
    run_id: str, trace_id: str, step_id: str, iteration: int, payload: Dict[str, Any]
) -> CEGISEvent:
    """Create CEGIS.Iter.End event."""
    event = CEGISEvent(
        trace_id=trace_id,
        run_id=run_id,
        step_id=step_id,
        type=EventType.CEGIS_ITER_END,
        payload={**payload, "iteration": iteration},
    )
    return event


def create_cegis_iter_refine_event(
    run_id: str,
    trace_id: str,
    step_id: str,
    iteration: int,
    reason: str,
    payload: Dict[str, Any],
) -> CEGISEvent:
    """Create CEGIS.Iter.Refine event."""
    event = CEGISEvent(
        trace_id=trace_id,
        run_id=run_id,
        step_id=step_id,
        type=EventType.CEGIS_ITER_REFINE,
        payload={**payload, "iteration": iteration, "reason": reason},
    )
    return event


def create_cegis_iter_converged_event(
    run_id: str, trace_id: str, step_id: str, iteration: int, payload: Dict[str, Any]
) -> CEGISEvent:
    """Create CEGIS.Iter.Converged event."""
    event = CEGISEvent(
        trace_id=trace_id,
        run_id=run_id,
        step_id=step_id,
        type=EventType.CEGIS_ITER_CONVERGED,
        payload={**payload, "iteration": iteration},
    )
    return event


def create_verify_attempt_event(
    run_id: str, trace_id: str, step_id: str, payload: Dict[str, Any]
) -> VerifyEvent:
    """Create Verify.Attempt event."""
    event = VerifyEvent(
        trace_id=trace_id,
        run_id=run_id,
        step_id=step_id,
        type=EventType.VERIFY_ATTEMPT,
        payload=payload,
    )
    return event


def create_verify_result_event(
    run_id: str, trace_id: str, step_id: str, ok: bool, payload: Dict[str, Any]
) -> VerifyEvent:
    """Create Verify.Result event."""
    event = VerifyEvent(
        trace_id=trace_id,
        run_id=run_id,
        step_id=step_id,
        type=EventType.VERIFY_RESULT,
        payload={**payload, "ok": ok},
    )
    return event


def create_budget_overrun_event(
    run_id: str, trace_id: str, step_id: str, budget_type: str, payload: Dict[str, Any]
) -> BudgetEvent:
    """Create Budget.Overrun event."""
    event = BudgetEvent(
        trace_id=trace_id,
        run_id=run_id,
        step_id=step_id,
        type=EventType.BUDGET_OVERRUN,
        payload={**payload, "budget_type": budget_type},
    )
    return event


def create_incident_event(
    run_id: str,
    trace_id: str,
    step_id: str,
    code: str,
    message: str,
    detail: Dict[str, Any],
) -> IncidentEvent:
    """Create Incident event."""
    event = IncidentEvent(
        trace_id=trace_id,
        run_id=run_id,
        step_id=step_id,
        type=EventType.INCIDENT,
        payload={"code": code, "message": message, "detail": detail},
    )
    return event


def create_pcap_emitted_event(
    run_id: str, trace_id: str, step_id: str, path: str, hash_value: str, size: int
) -> PCAPEvent:
    """Create PCAP.Emitted event."""
    event = PCAPEvent(
        trace_id=trace_id,
        run_id=run_id,
        step_id=step_id,
        type=EventType.PCAP_EMITTED,
        payload={"path": path, "hash": hash_value, "size": size},
    )
    return event


def create_metrics_snapshot_event(
    run_id: str, trace_id: str, step_id: str, metrics: Dict[str, Any]
) -> MetricsEvent:
    """Create Metrics.Snapshot event."""
    event = MetricsEvent(
        trace_id=trace_id,
        run_id=run_id,
        step_id=step_id,
        type=EventType.METRICS_SNAPSHOT,
        payload=metrics,
    )
    return event
