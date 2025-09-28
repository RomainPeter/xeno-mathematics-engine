from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from pefc.policy.factory import make_ids, make_risk
from pefc.policy.interfaces import ArmStats

log = logging.getLogger(__name__)


class InjectableSelector:
    """Selector using injectable IDS and risk strategies."""

    def __init__(
        self,
        bandit,
        diversity,
        ids_config: Dict[str, Any] = None,
        risk_config: Dict[str, Any] = None,
        overrides_file: str = None,
    ):
        self.bandit = bandit
        self.diversity = diversity

        # Load overrides if provided
        if overrides_file and Path(overrides_file).exists():
            with open(overrides_file) as f:
                overrides = json.load(f)
                ids_config = overrides.get("ids", ids_config or {})
                risk_config = overrides.get("risk", risk_config or {})

        # Use defaults if not provided
        ids_config = ids_config or {"name": "ucb", "params": {"c": 2.0}}
        risk_config = risk_config or {"name": "cvar", "params": {"alpha": 0.1}}

        # Create strategies
        self.ids = make_ids(ids_config["name"], **ids_config.get("params", {}))
        self.risk = make_risk(risk_config["name"], **risk_config.get("params", {}))

        self.ids_config = ids_config
        self.risk_config = risk_config
        self.overrides_file = overrides_file

        log.info(
            "InjectableSelector: using IDS=%s, Risk=%s",
            ids_config["name"],
            risk_config["name"],
        )

    def rank(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank candidates using diversity + IDS scoring."""
        # candidates: [{'id', 'V_hat', 'S_hat', 'info_gain','var','cost', 'diversity_key', ...}]
        diverse = self.diversity.select(candidates)

        # Convert to ArmStats for IDS selection
        arm_stats = []
        for c in diverse:
            # Create virtual arm stats from candidate info
            arm = ArmStats(
                arm_id=c.get("id", "unknown"),
                pulls=1,  # Virtual pull count
                reward_sum=c.get("S_hat", 0.0),
                reward_sq_sum=c.get("S_hat", 0.0) ** 2,
            )
            arm_stats.append(arm)

        # IDS selection
        if arm_stats:
            chosen_id = self.ids.select(arm_stats, context={"candidates": diverse})

            # Log decision
            log.info(
                "policy.select",
                extra={
                    "ids": self.ids_config["name"],
                    "risk": self.risk_config["name"],
                    "chosen": chosen_id,
                    "candidates_count": len(diverse),
                },
            )

            # Reorder based on IDS selection
            chosen_idx = next(
                (i for i, c in enumerate(diverse) if c.get("id") == chosen_id), 0
            )
            if chosen_idx > 0:
                diverse[0], diverse[chosen_idx] = diverse[chosen_idx], diverse[0]

        return diverse

    def update(
        self, cand_id: str, reward_samples: List[float], cost_samples: List[float]
    ):
        """Update bandit with risk-adjusted utility."""
        # Calculate risk-adjusted utility
        utility_samples = [r - c for r, c in zip(reward_samples, cost_samples)]
        u = self.risk.score(utility_samples)

        # Update bandit
        self.bandit.update(cand_id, u)

        log.debug("policy.update: cand_id=%s, risk_score=%.4f", cand_id, u)

    def get_scores(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get IDS and risk scores for candidates."""
        scores = []
        for c in candidates:
            # IDS score (using virtual arm stats)
            arm = ArmStats(
                arm_id=c.get("id", "unknown"),
                pulls=1,
                reward_sum=c.get("S_hat", 0.0),
                reward_sq_sum=c.get("S_hat", 0.0) ** 2,
            )
            ids_score = self.ids.select([arm])

            # Risk score
            reward_samples = c.get("reward_samples", [0.0])
            cost_samples = c.get("cost_samples", [0.0])
            utility_samples = [r - c for r, c in zip(reward_samples, cost_samples)]
            risk_score = self.risk.score(utility_samples)

            scores.append(
                {
                    "candidate_id": c.get("id"),
                    "ids_score": ids_score,
                    "risk_score": risk_score,
                    "ids_strategy": self.ids_config["name"],
                    "risk_strategy": self.risk_config["name"],
                }
            )

        return scores

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            "ids": self.ids_config,
            "risk": self.risk_config,
            "overrides_file": self.overrides_file,
        }
