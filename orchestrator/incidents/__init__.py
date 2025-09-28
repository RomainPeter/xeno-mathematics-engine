"""
Incident management for Orchestrator v1.
Provides FailReason emission and incident handling.
"""

from .failreason import FailReason, FailReasonType, FailReasonSeverity
from .incident_manager import IncidentManager, IncidentConfig
from .incident_emitter import IncidentEmitter

__all__ = [
    "FailReason",
    "FailReasonType",
    "FailReasonSeverity",
    "IncidentManager",
    "IncidentConfig",
    "IncidentEmitter",
]
