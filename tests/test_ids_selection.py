from __future__ import annotations
from pefc.policy.ids import UCB1, EpsilonGreedy, ThompsonSampling
from pefc.policy.interfaces import ArmStats


def test_ucb1_selection():
    """Test UCB1 selection strategy."""
    ids = UCB1(c=2.0)

    # Create test arms
    arms = [
        ArmStats(arm_id="arm1", pulls=10, reward_sum=5.0, reward_sq_sum=3.0),
        ArmStats(arm_id="arm2", pulls=5, reward_sum=3.0, reward_sq_sum=2.0),
        ArmStats(arm_id="arm3", pulls=1, reward_sum=0.0, reward_sq_sum=0.0),  # Never pulled
    ]

    # UCB1 should prefer unexplored arms
    selected = ids.select(arms)
    assert selected in ["arm1", "arm2", "arm3"]

    # With many pulls, should prefer higher mean
    arms_high_pulls = [
        ArmStats(arm_id="low", pulls=100, reward_sum=10.0, reward_sq_sum=5.0),
        ArmStats(arm_id="high", pulls=100, reward_sum=50.0, reward_sq_sum=25.0),
    ]
    selected = ids.select(arms_high_pulls)
    assert selected == "high"


def test_epsilon_greedy_selection():
    """Test epsilon-greedy selection strategy."""
    ids = EpsilonGreedy(eps=0.1)

    # Create test arms
    arms = [
        ArmStats(arm_id="arm1", pulls=10, reward_sum=5.0, reward_sq_sum=3.0),
        ArmStats(arm_id="arm2", pulls=5, reward_sum=3.0, reward_sq_sum=2.0),
    ]

    # Should select from available arms
    selected = ids.select(arms)
    assert selected in ["arm1", "arm2"]

    # Test multiple selections to check exploration
    selections = [ids.select(arms) for _ in range(100)]
    assert "arm1" in selections
    assert "arm2" in selections


def test_thompson_sampling_selection():
    """Test Thompson Sampling selection strategy."""
    ids = ThompsonSampling()

    # Create test arms
    arms = [
        ArmStats(arm_id="arm1", pulls=10, reward_sum=5.0, reward_sq_sum=3.0),
        ArmStats(arm_id="arm2", pulls=5, reward_sum=3.0, reward_sq_sum=2.0),
    ]

    # Should select from available arms
    selected = ids.select(arms)
    assert selected in ["arm1", "arm2"]

    # Test multiple selections
    selections = [ids.select(arms) for _ in range(10)]
    assert "arm1" in selections
    assert "arm2" in selections


def test_arm_stats_properties():
    """Test ArmStats properties."""
    arm = ArmStats(arm_id="test", pulls=10, reward_sum=5.0, reward_sq_sum=3.0)

    # Test mean calculation
    assert arm.mean == 0.5

    # Test variance calculation
    expected_var = 3.0 / 10 - 0.5**2
    assert abs(arm.variance - expected_var) < 1e-9

    # Test zero pulls
    arm_zero = ArmStats(arm_id="zero", pulls=0, reward_sum=0.0, reward_sq_sum=0.0)
    assert arm_zero.mean == 0.0
    assert arm_zero.variance == 0.0


def test_selection_with_context():
    """Test selection with context parameter."""
    ids = UCB1()

    arms = [
        ArmStats(arm_id="arm1", pulls=5, reward_sum=2.5, reward_sq_sum=1.5),
        ArmStats(arm_id="arm2", pulls=3, reward_sum=1.5, reward_sq_sum=0.8),
    ]

    # Should work with context (even if not used)
    context = {"step": 1, "temperature": 0.5}
    selected = ids.select(arms, context=context)
    assert selected in ["arm1", "arm2"]


def test_ucb1_exploration_bonus():
    """Test that UCB1 gives exploration bonus to unexplored arms."""
    ids = UCB1(c=2.0)

    # One arm never pulled, others pulled
    arms = [
        ArmStats(arm_id="explored", pulls=100, reward_sum=50.0, reward_sq_sum=25.0),
        ArmStats(arm_id="unexplored", pulls=0, reward_sum=0.0, reward_sq_sum=0.0),
    ]

    # UCB1 should prefer unexplored arm due to high bonus
    selected = ids.select(arms)
    assert selected == "unexplored"
