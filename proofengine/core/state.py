"""State management utilities for ProofEngine."""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, Iterable, List, Optional

from .hashing import hash_state
from .schemas import PCAP, VJustification, XState


def _normalise_collection(values: Optional[Iterable[str]]) -> List[str]:
    return list(dict.fromkeys(values or []))


def create_initial_state(
    hypotheses: Optional[Iterable[str]] = None,
    evidences: Optional[Iterable[str]] = None,
    obligations: Optional[Iterable[Any]] = None,
    artifacts: Optional[Iterable[str]] = None,
    sigma: Optional[Dict[str, Any]] = None,
) -> XState:
    """Create a canonical initial Χ state."""

    state = XState(
        H=_normalise_collection(hypotheses),
        E=_normalise_collection(evidences),
        K=list(obligations) if obligations else [],
        A=_normalise_collection(artifacts),
        Sigma=dict(sigma or {}),
    )
    state.state_hash = hash_state(state)
    return state


class StateManager:
    """Utility for snapshotting and mutating Χ state objects."""

    def __init__(self, initial_state: XState):
        self.current_state: XState = initial_state
        self.snapshots: Dict[str, XState] = {}
        self.journal: list[Dict[str, Any]] = []

    def snapshot(self) -> str:
        snapshot_id = str(uuid.uuid4())
        self.snapshots[snapshot_id] = copy.deepcopy(self.current_state)
        return snapshot_id

    def rollback(self, snapshot_id: str) -> bool:
        snapshot = self.snapshots.get(snapshot_id)
        if snapshot is None:
            return False
        self.current_state = copy.deepcopy(snapshot)
        return True

    def add_rule_from_incident(self, incident: PCAP, rule_type: str) -> None:
        """Augment the K component with a rule derived from a failing PCAP."""

        rule = {
            "type": rule_type,
            "trigger": incident.action or incident.operator,
            "obligations": incident.obligations,
            "verdict": incident.verdict,
        }
        self.current_state.K.append(rule)

    def record_action(self, action: str, verdict: str, cost: VJustification) -> None:
        entry = {
            "action": action,
            "verdict": verdict,
            "cost": cost.to_dict(),
        }
        self.journal.append(entry)
