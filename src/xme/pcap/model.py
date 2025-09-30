from __future__ import annotations
from typing import Dict, Optional
from pydantic import BaseModel
from datetime import datetime


class PCAPEntry(BaseModel):
    action: str
    actor: str
    obligations: Dict[str, str] = {}
    deltas: Dict[str, float] = {}
    timestamp: datetime
    psp_ref: Optional[str] = None
