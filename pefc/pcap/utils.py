from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_hash(obj: Any) -> str:
    """Generate canonical hash for object."""
    blob = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(blob).hexdigest()


def sum_v(*vs):
    """Sum multiple V vectors additively."""
    out = {}
    for v in vs:
        for k, val in (v or {}).items():
            if val is None:
                continue
            out[k] = out.get(k, 0.0) + float(val)
    return out
