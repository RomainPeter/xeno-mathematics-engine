"""
Structured event bus with correlation and JSON logging.
Extends the base event bus with structured event publishing.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .bus import EventBus, Event
from .schemas import EventSchema, EventBuilder, EventTypes


class StructuredEventBus(EventBus):
    """Event bus with structured event publishing and correlation."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.event_builder: Optional[EventBuilder] = None
        self._setup_logging_subscriber()

    def set_correlation_ids(self, trace_id: str, run_id: str) -> None:
        """Set correlation IDs for event publishing."""
        self.event_builder = EventBuilder(trace_id, run_id)

    def emit_structured(self, event: EventSchema) -> None:
        """Emit structured event with correlation."""
        # Convert to legacy event format for compatibility
        topic = f"{event.phase}.{event.type}"
        data = event.to_dict()

        # Emit legacy event
        self.emit(topic, **data)

        # Log structured event
        self._log_structured_event(event)

    def emit_ae_event(
        self,
        event_type: str,
        payload: Dict[str, Any] = None,
        timings: Dict[str, float] = None,
        level: str = "info",
    ) -> None:
        """Emit AE-specific structured event."""
        if not self.event_builder:
            raise RuntimeError("Correlation IDs not set")

        event = self.event_builder.create_ae_event(event_type, payload, timings, level)
        self.emit_structured(event)

    def emit_cegis_event(
        self,
        event_type: str,
        payload: Dict[str, Any] = None,
        timings: Dict[str, float] = None,
        level: str = "info",
    ) -> None:
        """Emit CEGIS-specific structured event."""
        if not self.event_builder:
            raise RuntimeError("Correlation IDs not set")

        event = self.event_builder.create_cegis_event(
            event_type, payload, timings, level
        )
        self.emit_structured(event)

    def emit_orchestrator_event(
        self,
        event_type: str,
        payload: Dict[str, Any] = None,
        timings: Dict[str, float] = None,
        level: str = "info",
    ) -> None:
        """Emit orchestrator-specific structured event."""
        if not self.event_builder:
            raise RuntimeError("Correlation IDs not set")

        event = self.event_builder.create_orchestrator_event(
            event_type, payload, timings, level
        )
        self.emit_structured(event)

    def emit_incident(
        self, incident_type: str, severity: str, context: Dict[str, Any]
    ) -> None:
        """Emit incident event."""
        payload = {
            "incident_type": incident_type,
            "severity": severity,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        }

        self.emit_orchestrator_event(
            EventTypes.INCIDENT_RAISED, payload=payload, level=severity
        )

    def emit_pcap(self, pcap_data: Dict[str, Any]) -> None:
        """Emit PCAP event."""
        payload = {
            "pcap_id": pcap_data.get("id"),
            "action": pcap_data.get("action"),
            "context_hash": pcap_data.get("context_hash"),
            "obligations": pcap_data.get("obligations", []),
            "timestamp": datetime.now().isoformat(),
        }

        self.emit_orchestrator_event(
            EventTypes.PCAP_EMITTED, payload=payload, level="info"
        )

    def emit_budget_warning(
        self, budget_type: str, current: float, limit: float
    ) -> None:
        """Emit budget warning."""
        payload = {
            "budget_type": budget_type,
            "current": current,
            "limit": limit,
            "percentage": (current / limit) * 100 if limit > 0 else 0,
            "timestamp": datetime.now().isoformat(),
        }

        self.emit_orchestrator_event(
            EventTypes.BUDGET_WARNING, payload=payload, level="warning"
        )

    def emit_budget_overrun(
        self, budget_type: str, current: float, limit: float
    ) -> None:
        """Emit budget overrun."""
        payload = {
            "budget_type": budget_type,
            "current": current,
            "limit": limit,
            "overrun": current - limit,
            "timestamp": datetime.now().isoformat(),
        }

        self.emit_orchestrator_event(
            EventTypes.BUDGET_OVERRUN, payload=payload, level="error"
        )

    def _setup_logging_subscriber(self) -> None:
        """Setup structured logging subscriber."""

        def log_handler(event: Event) -> None:
            # Log structured event as JSON
            log_data = {
                "timestamp": datetime.fromtimestamp(event.ts).isoformat(),
                "event": event.topic,
                "data": event.data,
            }

            # Determine log level
            level = logging.INFO
            if "error" in event.topic or "failed" in event.topic:
                level = logging.ERROR
            elif "warning" in event.topic or "timeout" in event.topic:
                level = logging.WARNING
            elif "debug" in event.topic:
                level = logging.DEBUG

            self.logger.log(level, json.dumps(log_data, ensure_ascii=False))

        # Subscribe to all events
        self.subscribe("*", log_handler)

    def _log_structured_event(self, event: EventSchema) -> None:
        """Log structured event with correlation."""
        log_data = {
            "timestamp": datetime.fromtimestamp(event.ts).isoformat(),
            "trace_id": event.trace_id,
            "run_id": event.run_id,
            "step_id": event.step_id,
            "phase": event.phase,
            "type": event.type,
            "level": event.level,
            "payload": event.payload,
            "timings": event.timings,
            "version": event.version,
        }

        if event.parent_step_id:
            log_data["parent_step_id"] = event.parent_step_id

        if event.correlation_data:
            log_data["correlation_data"] = event.correlation_data

        # Determine log level
        level = logging.INFO
        if event.level == "error" or event.level == "critical":
            level = logging.ERROR
        elif event.level == "warning":
            level = logging.WARNING
        elif event.level == "debug":
            level = logging.DEBUG

        self.logger.log(level, json.dumps(log_data, ensure_ascii=False))
