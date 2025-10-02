from __future__ import annotations

import importlib
import logging
from typing import Any, Dict, List

from pefc.capabilities.core import Capability
from pefc.errors import ConfigError

log = logging.getLogger(__name__)


def load_capability(spec: str, params: Dict[str, Any]) -> Capability:
    """Load capability from module spec."""
    # "pkg.mod:Class"
    if ":" not in spec:
        raise ConfigError(f"invalid capability spec: {spec}")
    mod, cls = spec.split(":", 1)
    if not (mod.startswith("pefc.") or mod.startswith("plugins.")):
        raise ConfigError(f"module not allowed: {mod}")
    C = getattr(importlib.import_module(mod), cls)
    return C(**(params or {}))


def build_capabilities(cfg: Dict[str, Any]) -> List[Capability]:
    """Build capabilities from configuration."""
    # cfg: { allowlist: [], denylist: [], registry: [{id, module, enabled, params}] }
    allow = set((cfg or {}).get("allowlist") or [])
    deny = set((cfg or {}).get("denylist") or [])
    caps: List[Capability] = []
    for item in (cfg or {}).get("registry", []):
        if not item.get("enabled", True):
            continue
        hid = item.get("id")
        spec = item.get("module")
        if not hid or not spec:
            raise ConfigError("capability missing id/module")
        if allow and hid not in allow:
            continue
        if hid in deny:
            continue
        cap = load_capability(spec, item.get("params") or {})
        if getattr(cap.meta, "id", None) != hid:
            log.warning(
                "capability.id.mismatch",
                extra={"cfg_id": hid, "meta_id": cap.meta.id},
            )
        caps.append(cap)
    return caps
