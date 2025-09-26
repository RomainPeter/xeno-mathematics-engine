from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class VJustification(BaseModel):
    time_ms: int = 0
    backtracks: int = 0
    audit_cost_ms: int = 0
    tech_debt: int = 0
    llm_time_ms: Optional[int] = None
    model: Optional[str] = None

class PCAP(BaseModel):
    ts: str
    operator: str
    case_id: str
    pre: Dict[str, Any]
    post: Dict[str, Any]
    obligations: List[str]
    justification: VJustification
    proof_state_hash: str
    toolchain: Dict[str, str]
    llm_meta: Optional[Dict[str, Any]] = None
    verdict: Optional[str] = None  # pass|fail

class XState(BaseModel):
    H: List[str] = []
    E: List[str] = []
    K: List[str] = []
    J: List[PCAP] = []
    A: List[str] = []
    Sigma: Dict[str, Any] = {}
