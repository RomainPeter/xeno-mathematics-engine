from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class TwoMorphism:
    source: str  # composite plan id π
    target: str  # fallback π'
    conditions: Dict[str, Any]  # e.g., {'FailReason':'LowCoverage', 'V.time_ms': {'<': 1000}}
    preference: Dict[str, Any]  # e.g., {'pareto': ['coverage','risk'], 'dominance':'weak'}
    actions: List[
        Dict[str, Any]
    ]  # e.g., [{'add_K': 'min_novelty>=0.3'}, {'replan_hint':'prefer Meet'}]


def choose_fallback(pi_id, fail_reason, catalog: Dict[str, TwoMorphism]):
    for tm in catalog.values():
        if tm.source == pi_id and tm.conditions.get("FailReason") == fail_reason:
            return tm.target, tm.actions
    return None, []
