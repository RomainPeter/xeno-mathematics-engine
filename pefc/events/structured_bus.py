"""
StructuredEventBus shim over the minimal EventBus for orchestrator compatibility.
Provides correlation IDs and simple emit helpers.
"""

import logging
from typing import Dict, Any, Optional

from .event_bus import EventBus, EventBusConfig
from .types import create_event, EventType, EventLevel


_TOPIC_TO_EVENT_TYPE = {
    "Orchestrator.Start": EventType.ORCHESTRATOR_START,
    "Orchestrator.End": EventType.ORCHESTRATOR_END,
    "AE.Step": EventType.AE_STEP,
    "AE.Concept.Emitted": EventType.AE_CONCEPT_EMITTED,
    "CEGIS.Iter.Start": EventType.CEGIS_ITER_START,
    "CEGIS.Iter.End": EventType.CEGIS_ITER_END,
    "CEGIS.Iter.Refine": EventType.CEGIS_ITER_REFINE,
    "CEGIS.Iter.Converged": EventType.CEGIS_ITER_CONVERGED,
    "Verify.Attempt": EventType.VERIFY_ATTEMPT,
    "Verify.Result": EventType.VERIFY_RESULT,
    "Budget.Overrun": EventType.BUDGET_OVERRUN,
    "Incident": EventType.INCIDENT,
    "PCAP.Emitted": EventType.PCAP_EMITTED,
    "Metrics.Snapshot": EventType.METRICS_SNAPSHOT,
}


class StructuredEventBus(EventBus):
    """Compatibility layer exposing emit_* helpers used by the orchestrator."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        config: Optional[EventBusConfig] = None,
    ):
        super().__init__(config=config)
        self.logger = logger or logging.getLogger(__name__)
        self._trace_id: Optional[str] = None
        self._run_id: Optional[str] = None

    def set_correlation_ids(self, trace_id: str, run_id: str) -> None:
        self._trace_id = trace_id
        self._run_id = run_id

    # Generic emitter compatible with orchestrator's expected API
    def emit(self, topic: str, **payload: Any) -> None:
        event_type = _TOPIC_TO_EVENT_TYPE.get(topic, EventType.METRICS_SNAPSHOT)
        event = create_event(
            event_type=event_type,
            payload={**payload},
            trace_id=self._trace_id or "",
            run_id=self._run_id or "",
        )
        # Best-effort enqueue
        self.publish_nowait(event)

    def emit_orchestrator_event(
        self,
        event_type: str,
        payload: Dict[str, Any] = None,
        timings: Dict[str, float] = None,
        level: str = "info",
    ) -> None:
        payload = payload or {}
        etype = (
            EventType.ORCHESTRATOR_START
            if event_type == "started"
            else EventType.ORCHESTRATOR_END
        )
        event = create_event(
            event_type=etype,
            payload={**payload, "timings": timings or {}},
            trace_id=self._trace_id or "",
            run_id=self._run_id or "",
        )
        self.publish_nowait(event)

    def emit_incident(
        self, incident_type: str, severity: str, context: Dict[str, Any]
    ) -> None:
        level = (
            EventLevel.ERROR if severity in ("error", "critical") else EventLevel.WARN
        )
        event = create_event(
            event_type=EventType.INCIDENT,
            payload={
                "code": incident_type,
                "message": incident_type,
                "detail": context,
                "severity": severity,
            },
            trace_id=self._trace_id or "",
            run_id=self._run_id or "",
            level=level,
        )
        self.publish_nowait(event)
