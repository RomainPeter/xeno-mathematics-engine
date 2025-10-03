from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, Literal, Optional

import orjson
from pydantic import BaseModel, ConfigDict


def canonical_dumps(obj: Any) -> bytes:
    return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class RunHeader(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    type: Literal["run_header"] = "run_header"
    run_id: str
    started_at: datetime
    tool: str = "xme"
    version: str = "0.0.1"


class PCAPEntry(BaseModel):
    type: Literal["action"] = "action"
    action: str
    actor: str
    level: Literal["S0", "S1", "S2"] = "S0"
    obligations: Dict[str, str] = {}
    deltas: Dict[str, float] = {}
    timestamp: datetime
    psp_ref: Optional[str] = None
    prev_hash: Optional[str] = None
    hash: Optional[str] = None

    def payload_for_hash(self) -> dict:
        # Exclude self.hash; include prev_hash for chaining
        d = self.model_dump()
        d.pop("hash", None)
        return d

    def compute_hash(self) -> str:
        return sha256_hex(canonical_dumps(self.payload_for_hash()))
