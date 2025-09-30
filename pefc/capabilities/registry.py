from __future__ import annotations
from typing import Dict, Any, List, Optional
import importlib
import logging
from pefc.capabilities.base import IncidentHandler
from pefc.errors import ConfigError

log = logging.getLogger(__name__)


class IncidentCapabilityRegistry:
    """Registry for incident handling capabilities."""

    def __init__(
        self,
        allowlist: Optional[List[str]] = None,
        denylist: Optional[List[str]] = None,
    ):
        self._handlers: Dict[str, IncidentHandler] = {}
        self.allowlist = set(allowlist or [])
        self.denylist = set(denylist or [])

    def register(self, handler: IncidentHandler):
        """Register a capability handler."""
        hid = handler.meta.id
        if self.allowlist and hid not in self.allowlist:
            log.info("capability.skipped.allowlist", extra={"id": hid})
            return
        if hid in self.denylist:
            log.info("capability.skipped.denylist", extra={"id": hid})
            return
        self._handlers[hid] = handler
        log.info(
            "capability.registered",
            extra={"id": hid, "provides": handler.meta.provides},
        )

    def load_from_config(self, cfg: Dict[str, Any]):
        """Load handlers from configuration."""
        # cfg shape:
        # capabilities:
        #   allowlist: [hs-tree, opa-rego]
        #   registry:
        #     - id: hs-tree
        #       module: pefc.capabilities.handlers.hstree:HSTreeHandler
        #       enabled: true
        #       params: { depth: 3 }
        #     - id: opa-rego
        #       module: pefc.capabilities.handlers.opa:OPAHandler
        #       enabled: true
        #       params: { policy_dir: "policies" }
        # map allow/deny
        aw = cfg.get("allowlist") or []
        dw = cfg.get("denylist") or []
        if aw:
            self.allowlist = set(aw)
        if dw:
            self.denylist = set(dw)
        for item in cfg.get("registry", []):
            if not item.get("enabled", True):
                continue
            modspec = item.get("module")
            hid = item.get("id")
            if not modspec or not hid:
                raise ConfigError("capability item missing id/module")
            if self.allowlist and hid not in self.allowlist:
                continue
            if hid in self.denylist:
                continue
            handler = self._safe_import_construct(modspec, item.get("params") or {})
            if handler.meta.id != hid:
                log.warning(
                    "capability.id.mismatch",
                    extra={"cfg_id": hid, "meta_id": handler.meta.id},
                )
            self.register(handler)

    def _safe_import_construct(self, spec: str, params: Dict[str, Any]):
        """Safely import and construct handler from module spec."""
        # restricted import "pkg.module:Class"
        if ":" not in spec:
            raise ConfigError(f"invalid module spec: {spec}")
        mod, cls = spec.split(":", 1)
        if not mod.startswith("pefc.") and not mod.startswith("plugins."):
            raise ConfigError(f"module not allowed: {mod}")
        module = importlib.import_module(mod)
        ctor = getattr(module, cls)
        return ctor(**params)

    def list_handlers(self) -> List[Dict[str, Any]]:
        """List all registered handlers with metadata."""
        return [
            {
                "id": h.meta.id,
                "version": h.meta.version,
                "provides": h.meta.provides,
                "prereq_missing": h.check_prerequisites(),
            }
            for h in self._handlers.values()
        ]

    def select(self, incident: Dict[str, Any]) -> Optional[IncidentHandler]:
        """Select best handler for incident."""
        itype = incident.get("type")
        candidates: List[IncidentHandler] = [
            h for h in self._handlers.values() if h.can_handle(itype)
        ]
        candidates = [
            h for h in candidates if not h.check_prerequisites()
        ]  # keep only ready
        if not candidates:
            return None
        scored = [(h.score(incident), h) for h in candidates]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    def execute(
        self, incident: Dict[str, Any], ctx: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Execute best handler for incident."""
        h = self.select(incident)
        if not h:
            return {
                "status": "no-capability",
                "incident_type": incident.get("type"),
                "handlers": self.list_handlers(),
            }
        res = h.handle(incident, ctx or {})
        log.info(
            "capability.executed",
            extra={
                "handler": h.meta.id,
                "incident": incident.get("id"),
                "status": res.get("status"),
            },
        )
        return res
