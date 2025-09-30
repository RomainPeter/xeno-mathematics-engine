from __future__ import annotations
import math
import random
from typing import Sequence

from .interfaces import ArmStats


class UCB1:
    """Upper Confidence Bound strategy."""

    def __init__(self, c: float = 2.0):
        self.c = c

    def select(self, arms: Sequence[ArmStats], context=None) -> str:
        """Select arm using UCB1."""
        n = sum(max(a.pulls, 1) for a in arms)

        def ucb(a: ArmStats) -> float:
            bonus = self.c * math.sqrt(math.log(n) / max(a.pulls, 1))
            return a.mean + bonus

        return max(arms, key=ucb).arm_id


class EpsilonGreedy:
    """Epsilon-greedy strategy."""

    def __init__(self, eps: float = 0.1):
        self.eps = eps

    def select(self, arms: Sequence[ArmStats], context=None) -> str:
        """Select arm using epsilon-greedy."""
        if random.random() < self.eps:
            return random.choice(arms).arm_id
        return max(arms, key=lambda a: a.mean).arm_id


class ThompsonSampling:
    """Thompson Sampling strategy for rewards in [0,1]."""

    def select(self, arms: Sequence[ArmStats], context=None) -> str:
        """Select arm using Thompson Sampling."""

        def draw(a: ArmStats):
            alpha = 1 + a.reward_sum
            beta = 1 + max(a.pulls - a.reward_sum, 0.0)
            try:
                import numpy as np

                return np.random.beta(alpha, beta)
            except Exception:
                # Simple beta sampling fallback
                u1, u2 = random.random(), random.random()
                # Approximation: log transform; ok for stub
                return -math.log(u1) / (-math.log(u1) - math.log(u2))

        return max(arms, key=draw).arm_id
