"""
Event bus and structured telemetry for PEFC.
Provides EventBus, sinks, and event types for structured telemetry.
"""

from .event_bus import EventBus, EventBusConfig
from .event_bus import get_global_event_bus as get_event_bus
from .event_bus import publish_event, publish_event_nowait, set_global_event_bus
from .manifest import AuditManifest, MerkleTree
from .pcap import PCAPManager, PCAPSchema, PCAPWriter
from .sinks import EventSink, FileJSONLSink, MemorySink, RotatingFileSink, StdoutJSONLSink
from .structured_bus import StructuredEventBus
from .types import (
    AEEvent,
    BudgetEvent,
    CEGISEvent,
    Event,
    EventLevel,
    EventType,
    IncidentEvent,
    MetricsEvent,
    OrchestratorEvent,
    PCAPEvent,
    VerifyEvent,
    create_ae_concept_emitted_event,
    create_ae_step_event,
    create_budget_overrun_event,
    create_cegis_iter_converged_event,
    create_cegis_iter_end_event,
    create_cegis_iter_refine_event,
    create_cegis_iter_start_event,
    create_event,
    create_incident_event,
    create_metrics_snapshot_event,
    create_orchestrator_end_event,
    create_orchestrator_start_event,
    create_pcap_emitted_event,
    create_verify_attempt_event,
    create_verify_result_event,
)

__all__ = [
    "EventBus",
    "EventBusConfig",
    "StructuredEventBus",
    "get_event_bus",
    "set_global_event_bus",
    "publish_event",
    "publish_event_nowait",
    "StdoutJSONLSink",
    "FileJSONLSink",
    "MemorySink",
    "EventSink",
    "RotatingFileSink",
    "EventType",
    "EventLevel",
    "Event",
    "OrchestratorEvent",
    "AEEvent",
    "CEGISEvent",
    "VerifyEvent",
    "BudgetEvent",
    "IncidentEvent",
    "PCAPEvent",
    "MetricsEvent",
    "create_event",
    "create_orchestrator_start_event",
    "create_orchestrator_end_event",
    "create_ae_step_event",
    "create_ae_concept_emitted_event",
    "create_cegis_iter_start_event",
    "create_cegis_iter_end_event",
    "create_cegis_iter_refine_event",
    "create_cegis_iter_converged_event",
    "create_verify_attempt_event",
    "create_verify_result_event",
    "create_budget_overrun_event",
    "create_incident_event",
    "create_pcap_emitted_event",
    "create_metrics_snapshot_event",
    "AuditManifest",
    "MerkleTree",
    "PCAPWriter",
    "PCAPSchema",
    "PCAPManager",
]
