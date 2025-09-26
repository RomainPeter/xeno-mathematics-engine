"""Stochastic generation helpers used by tests and orchestrator."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from proofengine.core.schemas import ActionVariant, PatchProposal

from .mutators import ActionGenerator


class StochasticGenerator:
    """High level entry point wrapping the ActionGenerator utility."""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self.action_generator = ActionGenerator(seed)
        self.generation_history: List[Dict[str, Any]] = []

    def propose_actions(
        self,
        goal: str,
        obligations: List[Dict[str, Any]],
        seed: Optional[int] = None,
        k: int = 3,
    ) -> List[ActionVariant]:
        actions = self.action_generator.propose_actions(goal, obligations, seed=seed or self.seed, k=k)
        self.generation_history.extend(
            {
                "action_id": action.action_id,
                "timestamp": self._get_timestamp(),
                "confidence": action.confidence,
            }
            for action in actions
        )
        return actions

    def propose_variants(
        self,
        task: str,
        context: str,
        obligations: List[str],
        k: int = 3,
    ) -> List[PatchProposal]:
        actions = self.propose_actions(task, [{"policy": ob} for ob in obligations], k=k)
        variants: List[PatchProposal] = []
        for action in actions:
            variants.append(
                PatchProposal(
                    patch_unified=action.patch,
                    rationale=action.description,
                    predicted_obligations_satisfied=list(obligations),
                    risk_score=1.0 - action.confidence,
                    notes="generated locally",
                )
            )
        return variants

    def clear_history(self) -> None:
        self.generation_history = []

    def get_generation_stats(self) -> Dict[str, Any]:
        if not self.generation_history:
            return {"total_generations": 0}
        total = len(self.generation_history)
        avg_conf = sum(item["confidence"] for item in self.generation_history) / total
        return {"total_generations": total, "average_confidence": avg_conf}

    def _get_timestamp(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())