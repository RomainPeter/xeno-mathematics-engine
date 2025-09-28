from __future__ import annotations
import math
from typing import Sequence


class MeanRisk:
    """Neutral risk scorer (mean)."""

    def __init__(self):
        pass

    def score(self, samples: Sequence[float]) -> float:
        """Return mean of samples."""
        return sum(samples) / len(samples) if samples else float("-inf")


class CVaRRisk:
    """Conditional Value at Risk scorer."""

    def __init__(self, alpha: float = 0.1):
        self.alpha = max(1e-6, min(alpha, 0.5))

    def score(self, samples: Sequence[float]) -> float:
        """Return CVaR (lower tail) of samples."""
        if not samples:
            return float("-inf")
        xs = sorted(samples)
        k = max(1, int(math.ceil(self.alpha * len(xs))))
        tail = xs[:k]  # lower tail (risk)
        return sum(tail) / len(tail)


class EntropicRisk:
    """Entropic risk scorer."""

    def __init__(self, lam: float = 1.0):
        self.lam = lam

    def score(self, samples: Sequence[float]) -> float:
        """Return entropic risk score."""
        if not samples:
            return float("-inf")
        lam = self.lam
        # -1/λ log E[exp(-λX)] — smaller = more conservative
        m = sum(math.exp(-lam * x) for x in samples) / len(samples)
        return (-1.0 / lam) * math.log(max(m, 1e-300))


class SemiVarianceRisk:
    """Semi-variance risk scorer."""

    def __init__(self, target: float = 0.0):
        self.target = target

    def score(self, samples: Sequence[float]) -> float:
        """Return mean minus semi-variance penalty."""
        if not samples:
            return float("-inf")
        neg = [max(0.0, self.target - x) ** 2 for x in samples]
        pen = sum(neg) / len(neg)
        return (sum(samples) / len(samples)) - pen
