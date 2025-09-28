from __future__ import annotations
import logging
from pefc.capabilities.registry import IncidentCapabilityRegistry

log = logging.getLogger(__name__)


def build_registry(cfg) -> IncidentCapabilityRegistry:
    """Build capabilities registry from configuration."""
    reg = IncidentCapabilityRegistry()
    caps_cfg = getattr(cfg, "capabilities", None) or {}
    reg.load_from_config(caps_cfg)
    log.info("capabilities.loaded", extra={"handlers": reg.list_handlers()})
    return reg
