from __future__ import annotations
from typing import Protocol, Sequence, Mapping, Any
from dataclasses import dataclass


@dataclass
class ArmStats:
    """Statistics for a multi-armed bandit arm."""

    arm_id: str
    pulls: int
    reward_sum: float
    reward_sq_sum: float

    @property
    def mean(self) -> float:
        """Mean reward for this arm."""
        return self.reward_sum / max(self.pulls, 1)

    @property
    def variance(self) -> float:
        """Variance of rewards for this arm."""
        m = self.mean
        return max(self.reward_sq_sum / max(self.pulls, 1) - m * m, 0.0)


class RiskScorer(Protocol):
    """Protocol for risk scoring strategies."""

    def score(self, samples: Sequence[float]) -> float:
        """Score a sequence of samples according to risk strategy."""
        ...


class IDSStrategy(Protocol):
    """Protocol for IDS (Information-Directed Sampling) strategies."""

    def select(self, arms: Sequence[ArmStats], context: Mapping[str, Any] | None = None) -> str:
        """Select an arm based on the strategy."""
        ...
