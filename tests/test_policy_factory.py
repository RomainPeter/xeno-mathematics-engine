from __future__ import annotations
import pytest
from pefc.policy.factory import make_risk, make_ids


def test_make_risk_basic():
    """Test basic risk scorer creation."""
    # Test mean risk
    risk = make_risk("mean")
    assert risk.score([1.0, 2.0, 3.0]) == 2.0

    # Test CVaR risk
    risk = make_risk("cvar", alpha=0.1)
    assert hasattr(risk, "alpha")
    assert risk.alpha == 0.1

    # Test entropic risk
    risk = make_risk("entropic", lam=2.0)
    assert hasattr(risk, "lam")
    assert risk.lam == 2.0

    # Test semi-variance risk
    risk = make_risk("semivar", target=1.0)
    assert hasattr(risk, "target")
    assert risk.target == 1.0


def test_make_risk_aliases():
    """Test risk scorer aliases."""
    # Test aliases
    risk1 = make_risk("mean")
    risk2 = make_risk("neutral")
    assert type(risk1) == type(risk2)

    risk1 = make_risk("cvar")
    risk2 = make_risk("cv@r")
    assert type(risk1) == type(risk2)

    risk1 = make_risk("entropic")
    risk2 = make_risk("exp")
    assert type(risk1) == type(risk2)

    risk1 = make_risk("semivar")
    risk2 = make_risk("semivariance")
    assert type(risk1) == type(risk2)


def test_make_risk_unknown():
    """Test error on unknown risk scorer."""
    with pytest.raises(ValueError, match="unknown RiskScorer"):
        make_risk("unknown")


def test_make_ids_basic():
    """Test basic IDS strategy creation."""
    # Test UCB
    ids = make_ids("ucb", c=1.5)
    assert hasattr(ids, "c")
    assert ids.c == 1.5

    # Test epsilon-greedy
    ids = make_ids("epsilon", eps=0.2)
    assert hasattr(ids, "eps")
    assert ids.eps == 0.2

    # Test Thompson sampling
    ids = make_ids("thompson")
    assert hasattr(ids, "select")


def test_make_ids_aliases():
    """Test IDS strategy aliases."""
    # Test aliases
    ids1 = make_ids("epsilon")
    ids2 = make_ids("eps")
    ids3 = make_ids("epsilon-greedy")
    assert type(ids1) == type(ids2) == type(ids3)

    ids1 = make_ids("thompson")
    ids2 = make_ids("ts")
    assert type(ids1) == type(ids2)


def test_make_ids_unknown():
    """Test error on unknown IDS strategy."""
    with pytest.raises(ValueError, match="unknown IDSStrategy"):
        make_ids("unknown")
