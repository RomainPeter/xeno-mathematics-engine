"""
Tests for policy selection wrapper.
"""

import pytest
from orchestrator.policy.select import PolicySelector, create_policy_selector


class TestPolicySelector:
    """Test cases for Policy Selector."""

    @pytest.fixture
    def mock_candidates(self):
        """Create mock candidates for testing."""
        return [
            {
                "id": "candidate_1",
                "features": [1.0, 2.0, 3.0],
                "diversity_key": "key_1",
                "confidence": 0.8,
                "metadata": {"type": "implication"},
            },
            {
                "id": "candidate_2",
                "features": [2.0, 3.0, 4.0],
                "diversity_key": "key_2",
                "confidence": 0.7,
                "metadata": {"type": "implication"},
            },
            {
                "id": "candidate_3",
                "features": [3.0, 4.0, 5.0],
                "diversity_key": "key_1",
                "confidence": 0.9,
                "metadata": {"type": "implication"},
            },
            {
                "id": "candidate_4",
                "features": [4.0, 5.0, 6.0],
                "diversity_key": "key_3",
                "confidence": 0.6,
                "metadata": {"type": "implication"},
            },
        ]

    def test_policy_selector_initialization(self):
        """Test policy selector initialization."""
        selector = PolicySelector(bandit_type="linucb", diversity_type="dpp")

        assert selector.bandit_type == "linucb"
        assert selector.diversity_type == "dpp"
        assert selector.bandit is not None
        assert selector.diversity is not None
        assert selector.total_selections == 0

    def test_select_candidates(self, mock_candidates):
        """Test candidate selection."""
        selector = PolicySelector(bandit_type="linucb", diversity_type="dpp")

        selected = selector.select_candidates(mock_candidates, k=2)

        assert len(selected) == 2
        assert all("id" in candidate for candidate in selected)
        assert selector.total_selections == 1

    def test_update_policy(self, mock_candidates):
        """Test policy update."""
        selector = PolicySelector(bandit_type="linucb", diversity_type="dpp")

        # Select candidates
        selected = selector.select_candidates(mock_candidates, k=2)

        # Update with feedback
        rewards = [0.8, 0.6]
        costs = [0.1, 0.2]

        selector.update_policy(selected, rewards, costs)

        # Check that update was recorded
        assert len(selector.selection_history) >= 2  # Selection + update

    def test_get_policy_stats(self, mock_candidates):
        """Test policy statistics."""
        selector = PolicySelector(bandit_type="linucb", diversity_type="dpp")

        # Perform some selections
        selector.select_candidates(mock_candidates, k=2)
        selector.select_candidates(mock_candidates, k=1)

        stats = selector.get_policy_stats()

        assert "bandit_type" in stats
        assert "diversity_type" in stats
        assert "total_selections" in stats
        assert "bandit_stats" in stats
        assert "diversity_stats" in stats
        assert stats["total_selections"] == 2

    def test_thompson_sampling_selector(self, mock_candidates):
        """Test Thompson Sampling selector."""
        selector = PolicySelector(bandit_type="thompson", diversity_type="submodular")

        selected = selector.select_candidates(mock_candidates, k=2)

        assert len(selected) == 2
        assert selector.bandit_type == "thompson"
        assert selector.diversity_type == "submodular"

    def test_selection_with_context(self, mock_candidates):
        """Test selection with context."""
        selector = PolicySelector(bandit_type="linucb", diversity_type="dpp")

        context = {"features": [0.5, 0.3, 0.8], "metadata": {"domain": "regtech"}}

        selected = selector.select_candidates(mock_candidates, k=2, context=context)

        assert len(selected) == 2
        assert selector.total_selections == 1

    def test_empty_candidates(self):
        """Test selection with empty candidates."""
        selector = PolicySelector()

        selected = selector.select_candidates([], k=2)

        assert selected == []
        assert selector.total_selections == 0

    def test_k_greater_than_candidates(self, mock_candidates):
        """Test selection when k > number of candidates."""
        selector = PolicySelector()

        selected = selector.select_candidates(mock_candidates, k=10)

        assert len(selected) == len(mock_candidates)
        assert selector.total_selections == 1


class TestConvenienceFunction:
    """Test convenience function."""

    def test_create_policy_selector(self):
        """Test create_policy_selector function."""
        selector = create_policy_selector(
            bandit_type="linucb",
            diversity_type="dpp",
            bandit_params={"alpha": 1.0, "d": 5},
            diversity_params={"lambda_param": 1.0},
        )

        assert selector.bandit_type == "linucb"
        assert selector.diversity_type == "dpp"
        assert selector.bandit is not None
        assert selector.diversity is not None


if __name__ == "__main__":
    # Run tests directly
    import sys

    sys.path.insert(0, ".")

    print("Running Policy Selection Tests...")

    # Test policy selector
    print("Testing Policy Selector...")
    try:
        selector = PolicySelector(bandit_type="linucb", diversity_type="dpp")
        print("✅ Policy Selector initialized")

        # Test candidates
        candidates = [
            {
                "id": "test_1",
                "features": [1.0, 2.0, 3.0],
                "diversity_key": "key_1",
                "confidence": 0.8,
            },
            {
                "id": "test_2",
                "features": [2.0, 3.0, 4.0],
                "diversity_key": "key_2",
                "confidence": 0.7,
            },
        ]

        # Test selection
        selected = selector.select_candidates(candidates, k=1)
        print(f"✅ Selected {len(selected)} candidates")

        # Test update
        rewards = [0.8]
        costs = [0.1]
        selector.update_policy(selected, rewards, costs)
        print("✅ Policy updated with feedback")

        # Test stats
        stats = selector.get_policy_stats()
        print(f"✅ Policy stats: {stats['total_selections']} selections")

    except Exception as e:
        print(f"❌ Policy Selector test failed: {e}")

    # Test convenience function
    print("Testing convenience function...")
    try:
        selector = create_policy_selector(
            bandit_type="thompson", diversity_type="submodular"
        )
        print("✅ Convenience function completed")
        print(f"✅ Selector type: {selector.bandit_type}/{selector.diversity_type}")

    except Exception as e:
        print(f"❌ Convenience function test failed: {e}")

    print("✅ Policy selection tests completed!")
