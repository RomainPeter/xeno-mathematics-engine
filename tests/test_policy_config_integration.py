from __future__ import annotations

import pytest

from pefc.config.model import RootConfig
from pefc.policy.factory import make_ids, make_risk
from pefc.policy.interfaces import ArmStats


def test_config_loading():
    """Test loading policy configuration."""
    # Test default config
    config = RootConfig()
    assert hasattr(config, "policy")
    assert config.policy.ids.name == "ucb"
    assert config.policy.risk.name == "mean"

    # Test custom config
    config_data = {
        "policy": {
            "ids": {"name": "epsilon", "params": {"eps": 0.2}},
            "risk": {"name": "cvar", "params": {"alpha": 0.1}},
        }
    }
    config = RootConfig(**config_data)
    assert config.policy.ids.name == "epsilon"
    assert config.policy.ids.params["eps"] == 0.2
    assert config.policy.risk.name == "cvar"
    assert config.policy.risk.params["alpha"] == 0.1


def test_factory_integration():
    """Test factory integration with config."""
    # Test IDS creation
    ids = make_ids("ucb", c=1.5)
    assert hasattr(ids, "c")
    assert ids.c == 1.5

    # Test risk creation
    risk = make_risk("cvar", alpha=0.2)
    assert hasattr(risk, "alpha")
    assert risk.alpha == 0.2


def test_strategy_swapping():
    """Test that strategies can be swapped via config."""
    # Test UCB1
    ids_ucb = make_ids("ucb", c=2.0)
    arms = [
        ArmStats(arm_id="arm1", pulls=5, reward_sum=2.5, reward_sq_sum=1.5),
        ArmStats(arm_id="arm2", pulls=3, reward_sum=1.5, reward_sq_sum=0.8),
    ]
    selected_ucb = ids_ucb.select(arms)

    # Test epsilon-greedy
    ids_eps = make_ids("epsilon", eps=0.1)
    selected_eps = ids_eps.select(arms)

    # Both should select valid arms
    assert selected_ucb in ["arm1", "arm2"]
    assert selected_eps in ["arm1", "arm2"]

    # Test risk swapping
    risk_mean = make_risk("mean")
    risk_cvar = make_risk("cvar", alpha=0.1)

    samples = [0.1, 0.3, 0.5, 0.7, 0.9]
    score_mean = risk_mean.score(samples)
    score_cvar = risk_cvar.score(samples)

    # CVaR should be more conservative
    assert score_cvar <= score_mean


def test_end_to_end_selection():
    """Test end-to-end selection process."""
    # Create strategies
    ids = make_ids("ucb", c=2.0)
    risk = make_risk("cvar", alpha=0.1)

    # Create test arms
    arms = [
        ArmStats(arm_id="arm1", pulls=10, reward_sum=5.0, reward_sq_sum=3.0),
        ArmStats(arm_id="arm2", pulls=5, reward_sum=3.0, reward_sq_sum=2.0),
    ]

    # Select arm
    selected = ids.select(arms)
    assert selected in ["arm1", "arm2"]

    # Score samples
    samples = [0.1, 0.3, 0.5, 0.7, 0.9]
    score = risk.score(samples)
    assert isinstance(score, float)
    assert not (score != score)  # Not NaN


def test_config_validation():
    """Test configuration validation."""
    # Test valid config
    config_data = {
        "policy": {
            "ids": {"name": "ucb", "params": {"c": 2.0}},
            "risk": {"name": "cvar", "params": {"alpha": 0.1}},
        }
    }
    config = RootConfig(**config_data)
    assert config.policy.ids.name == "ucb"
    assert config.policy.risk.name == "cvar"

    # Test invalid strategy names (should be caught by factory)
    with pytest.raises(ValueError, match="unknown IDSStrategy"):
        make_ids("invalid")

    with pytest.raises(ValueError, match="unknown RiskScorer"):
        make_risk("invalid")


def test_parameter_passing():
    """Test parameter passing to strategies."""
    # Test IDS parameters
    ids = make_ids("epsilon", eps=0.3)
    assert ids.eps == 0.3

    # Test risk parameters
    risk = make_risk("entropic", lam=2.0)
    assert risk.lam == 2.0

    # Test multiple parameters
    risk = make_risk("semivar", target=0.5)
    assert risk.target == 0.5
