"""
Incident management for Orchestrator v1.
Provides FailReason emission and incident handling.
"""

from .failreason import FailReason, FailReasonSeverity, FailReasonType
from .incident_emitter import IncidentEmitter
from .incident_manager import IncidentConfig, IncidentManager

__all__ = [
    "FailReason",
    "FailReasonType",
    "FailReasonSeverity",
    "IncidentManager",
    "IncidentConfig",
    "IncidentEmitter",
]
