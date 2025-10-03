from __future__ import annotations

from typing import Any

from .ids import UCB1, EpsilonGreedy, ThompsonSampling
from .risk import CVaRRisk, EntropicRisk, MeanRisk, SemiVarianceRisk


def make_risk(name: str, **kw: Any):
    """Create risk scorer by name."""
    name = name.lower()
    if name in ("mean", "neutral"):
        return MeanRisk()
    if name in ("cvar", "cv@r"):
        return CVaRRisk(**kw)
    if name in ("entropic", "exp"):
        return EntropicRisk(**kw)
    if name in ("semivar", "semivariance"):
        return SemiVarianceRisk(**kw)
    raise ValueError(f"unknown RiskScorer: {name}")


def make_ids(name: str, **kw: Any):
    """Create IDS strategy by name."""
    name = name.lower()
    if name == "ucb":
        return UCB1(**kw)
    if name in ("eps", "epsilon", "epsilon-greedy"):
        return EpsilonGreedy(**kw)
    if name in ("thompson", "ts"):
        return ThompsonSampling()
    raise ValueError(f"unknown IDSStrategy: {name}")
