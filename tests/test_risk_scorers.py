from __future__ import annotations

from pefc.policy.risk import CVaRRisk, EntropicRisk, MeanRisk, SemiVarianceRisk


def test_mean_risk():
    """Test mean risk scorer."""
    risk = MeanRisk()

    # Basic functionality
    assert risk.score([1.0, 2.0, 3.0]) == 2.0
    assert risk.score([0.0]) == 0.0

    # Empty samples
    assert risk.score([]) == float("-inf")


def test_cvar_risk():
    """Test CVaR risk scorer."""
    risk = CVaRRisk(alpha=0.1)

    # Test with sorted samples (worst 10%)
    samples = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    score = risk.score(samples)

    # CVaR should be <= mean for distributions with left tail
    mean_score = sum(samples) / len(samples)
    assert score <= mean_score

    # Empty samples
    assert risk.score([]) == float("-inf")

    # Test alpha bounds
    risk_high = CVaRRisk(alpha=0.6)
    risk_low = CVaRRisk(alpha=0.01)
    assert risk_high.alpha == 0.5  # Clamped
    assert risk_low.alpha == 0.01  # Not clamped (within bounds)


def test_entropic_risk():
    """Test entropic risk scorer."""
    risk = EntropicRisk(lam=1.0)

    # Test with samples
    samples = [0.1, 0.5, 0.9]
    score = risk.score(samples)

    # Entropic should be more conservative than mean
    mean_score = sum(samples) / len(samples)
    assert score <= mean_score

    # Higher lambda should be more conservative
    risk_high = EntropicRisk(lam=2.0)
    score_high = risk_high.score(samples)
    assert score_high <= score

    # Empty samples
    assert risk.score([]) == float("-inf")


def test_semi_variance_risk():
    """Test semi-variance risk scorer."""
    risk = SemiVarianceRisk(target=0.5)

    # Test with samples
    samples = [0.3, 0.4, 0.6, 0.7]
    score = risk.score(samples)

    # Should penalize deviations below target
    mean_score = sum(samples) / len(samples)
    assert score <= mean_score

    # Empty samples
    assert risk.score([]) == float("-inf")


def test_risk_properties():
    """Test risk scorer properties."""
    samples = [0.1, 0.3, 0.5, 0.7, 0.9]

    # Mean should be neutral
    mean_risk = MeanRisk()
    mean_score = mean_risk.score(samples)
    expected_mean = sum(samples) / len(samples)
    assert abs(mean_score - expected_mean) < 1e-9

    # CVaR should be more conservative
    cvar_risk = CVaRRisk(alpha=0.2)
    cvar_score = cvar_risk.score(samples)
    assert cvar_score <= mean_score

    # Entropic should be more conservative
    entropic_risk = EntropicRisk(lam=1.0)
    entropic_score = entropic_risk.score(samples)
    assert entropic_score <= mean_score
