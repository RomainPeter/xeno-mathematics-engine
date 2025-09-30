"""
Tests for Bandit LinUCB + DPP selection.
"""

import pytest
from policy.bandit import LinUCB, ThompsonSampling, BanditContext
from policy.diversity import (
    DPPSelector,
    SubmodularSelector,
    DiversityItem,
)


class TestLinUCB:
    """Test cases for LinUCB bandit."""

    @pytest.fixture
    def bandit(self):
        """Create LinUCB bandit for testing."""
        return LinUCB(alpha=1.0, d=5)

    def test_bandit_initialization(self, bandit):
        """Test bandit initialization."""
        assert bandit.alpha == 1.0
        assert bandit.d == 5
        assert bandit.total_selections == 0
        assert bandit.total_rewards == 0.0

    def test_select_action(self, bandit):
        """Test action selection."""
        context = BanditContext(features=[1.0, 2.0, 3.0, 4.0, 5.0], metadata={"test": "context"})

        candidates = [
            {"id": "candidate1", "features": [1.0, 2.0, 3.0, 4.0, 5.0]},
            {"id": "candidate2", "features": [2.0, 3.0, 4.0, 5.0, 6.0]},
            {"id": "candidate3", "features": [0.5, 1.5, 2.5, 3.5, 4.5]},
        ]

        action = bandit.select_action(context, candidates)

        assert action.id in ["candidate1", "candidate2", "candidate3"]
        assert action.confidence > 0
        assert action.selection_method == "LinUCB"
        assert len(action.features) == 5

    def test_update_bandit(self, bandit):
        """Test bandit update."""
        context = BanditContext(features=[1.0, 2.0, 3.0, 4.0, 5.0])
        candidates = [{"id": "test", "features": [1.0, 2.0, 3.0, 4.0, 5.0]}]

        action = bandit.select_action(context, candidates)

        # Update with reward
        bandit.update(action, reward=0.8, cost=0.1)

        assert bandit.total_rewards == 0.8
        assert len(bandit.selection_history) > 0

    def test_statistics(self, bandit):
        """Test bandit statistics."""
        context = BanditContext(features=[1.0, 2.0, 3.0, 4.0, 5.0])
        candidates = [{"id": "test", "features": [1.0, 2.0, 3.0, 4.0, 5.0]}]

        action = bandit.select_action(context, candidates)
        bandit.update(action, reward=0.8)

        stats = bandit.get_statistics()

        assert stats["total_selections"] == 1
        assert stats["total_rewards"] == 0.8
        assert stats["average_reward"] == 0.8
        assert "action_counts" in stats


class TestThompsonSampling:
    """Test cases for Thompson Sampling bandit."""

    @pytest.fixture
    def bandit(self):
        """Create Thompson Sampling bandit for testing."""
        return ThompsonSampling(d=5, nu=1.0)

    def test_bandit_initialization(self, bandit):
        """Test bandit initialization."""
        assert bandit.d == 5
        assert bandit.nu == 1.0
        assert bandit.total_selections == 0
        assert bandit.total_rewards == 0.0

    def test_select_action(self, bandit):
        """Test action selection."""
        context = BanditContext(features=[1.0, 2.0, 3.0, 4.0, 5.0], metadata={"test": "context"})

        candidates = [
            {"id": "candidate1", "features": [1.0, 2.0, 3.0, 4.0, 5.0]},
            {"id": "candidate2", "features": [2.0, 3.0, 4.0, 5.0, 6.0]},
        ]

        action = bandit.select_action(context, candidates)

        assert action.id in ["candidate1", "candidate2"]
        assert action.selection_method == "ThompsonSampling"
        assert len(action.features) == 5

    def test_update_bandit(self, bandit):
        """Test bandit update."""
        context = BanditContext(features=[1.0, 2.0, 3.0, 4.0, 5.0])
        candidates = [{"id": "test", "features": [1.0, 2.0, 3.0, 4.0, 5.0]}]

        action = bandit.select_action(context, candidates)
        bandit.update(action, reward=0.9)

        assert bandit.total_rewards == 0.9
        assert len(bandit.selection_history) > 0


class TestDPPSelector:
    """Test cases for DPP selector."""

    @pytest.fixture
    def selector(self):
        """Create DPP selector for testing."""
        return DPPSelector(lambda_param=1.0, kernel_type="rbf")

    @pytest.fixture
    def test_items(self):
        """Create test items for diversity selection."""
        items = []
        for i in range(10):
            item = DiversityItem(
                id=f"item_{i}",
                features=[float(i), float(i + 1), float(i + 2)],
                diversity_key=f"key_{i % 3}",
                metadata={"test": f"item_{i}"},
            )
            items.append(item)
        return items

    def test_selector_initialization(self, selector):
        """Test selector initialization."""
        assert selector.lambda_param == 1.0
        assert selector.kernel_type == "rbf"
        assert selector.total_selections == 0

    def test_select_diverse_items(self, selector, test_items):
        """Test diverse item selection."""
        selection = selector.select_diverse_items(test_items, k=3)

        assert len(selection.selected_items) == 3
        assert selection.diversity_score > 0
        assert selection.selection_method == "DPP"

        # Check that all selected items are from the input
        selected_ids = [item.id for item in selection.selected_items]
        input_ids = [item.id for item in test_items]
        assert all(item_id in input_ids for item_id in selected_ids)

    def test_select_with_diversity_key(self, selector, test_items):
        """Test selection with diversity key filter."""
        selection = selector.select_diverse_items(test_items, k=2, diversity_key="key_0")

        assert len(selection.selected_items) <= 2
        assert selection.diversity_score > 0

        # Check that all selected items have the specified diversity key
        for item in selection.selected_items:
            assert item.diversity_key == "key_0"

    def test_statistics(self, selector, test_items):
        """Test selector statistics."""
        selection = selector.select_diverse_items(test_items, k=3)

        stats = selector.get_statistics()

        assert stats["total_selections"] == 1
        assert stats["average_diversity_score"] > 0
        assert stats["max_diversity_score"] > 0
        assert "diversity_score_std" in stats


class TestSubmodularSelector:
    """Test cases for Submodular selector."""

    @pytest.fixture
    def selector(self):
        """Create Submodular selector for testing."""
        return SubmodularSelector(alpha=1.0, beta=0.5)

    @pytest.fixture
    def test_items(self):
        """Create test items for diversity selection."""
        items = []
        for i in range(8):
            item = DiversityItem(
                id=f"item_{i}",
                features=[float(i), float(i + 1), float(i + 2)],
                diversity_key=f"key_{i % 2}",
                metadata={"test": f"item_{i}"},
            )
            items.append(item)
        return items

    def test_selector_initialization(self, selector):
        """Test selector initialization."""
        assert selector.alpha == 1.0
        assert selector.beta == 0.5
        assert selector.total_selections == 0

    def test_select_diverse_items(self, selector, test_items):
        """Test diverse item selection."""
        selection = selector.select_diverse_items(test_items, k=4)

        assert len(selection.selected_items) == 4
        assert selection.diversity_score > 0
        assert selection.selection_method == "Submodular"

        # Check that all selected items are from the input
        selected_ids = [item.id for item in selection.selected_items]
        input_ids = [item.id for item in test_items]
        assert all(item_id in input_ids for item_id in selected_ids)

    def test_select_with_diversity_key(self, selector, test_items):
        """Test selection with diversity key filter."""
        selection = selector.select_diverse_items(test_items, k=2, diversity_key="key_0")

        assert len(selection.selected_items) <= 2
        assert selection.diversity_score > 0

        # Check that all selected items have the specified diversity key
        for item in selection.selected_items:
            assert item.diversity_key == "key_0"

    def test_statistics(self, selector, test_items):
        """Test selector statistics."""
        selection = selector.select_diverse_items(test_items, k=3)

        stats = selector.get_statistics()

        assert stats["total_selections"] == 1
        assert stats["average_diversity_score"] > 0
        assert stats["max_diversity_score"] > 0
        assert "diversity_score_std" in stats


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_dpp_select_function(self):
        """Test DPP select convenience function."""
        from policy.diversity import dpp_select

        candidates = [
            {"id": "item1", "features": [1.0, 2.0, 3.0], "diversity_key": "key1"},
            {"id": "item2", "features": [2.0, 3.0, 4.0], "diversity_key": "key2"},
            {"id": "item3", "features": [3.0, 4.0, 5.0], "diversity_key": "key1"},
        ]

        keys = ["key1", "key2"]
        selected = dpp_select(candidates, keys, k=2)

        assert len(selected) == 2
        assert all("id" in item for item in selected)

    def test_submodular_select_function(self):
        """Test submodular select convenience function."""
        from policy.diversity import submodular_select

        candidates = [
            {"id": "item1", "features": [1.0, 2.0, 3.0], "diversity_key": "key1"},
            {"id": "item2", "features": [2.0, 3.0, 4.0], "diversity_key": "key2"},
            {"id": "item3", "features": [3.0, 4.0, 5.0], "diversity_key": "key1"},
        ]

        keys = ["key1", "key2"]
        selected = submodular_select(candidates, keys, k=2)

        assert len(selected) == 2
        assert all("id" in item for item in selected)


if __name__ == "__main__":
    # Run tests directly
    import sys

    sys.path.insert(0, ".")

    print("Running Bandit + DPP Tests...")

    # Test LinUCB
    print("Testing LinUCB bandit...")
    try:
        bandit = LinUCB(alpha=1.0, d=5)
        print(f"✅ LinUCB initialized: alpha={bandit.alpha}, d={bandit.d}")

        context = BanditContext(features=[1.0, 2.0, 3.0, 4.0, 5.0])
        candidates = [{"id": "test", "features": [1.0, 2.0, 3.0, 4.0, 5.0]}]

        action = bandit.select_action(context, candidates)
        print(f"✅ Action selected: {action.id}, confidence={action.confidence:.3f}")

        bandit.update(action, reward=0.8)
        print(f"✅ Bandit updated: total_rewards={bandit.total_rewards}")

        stats = bandit.get_statistics()
        print(
            f"✅ Statistics: {stats['total_selections']} selections, {stats['total_rewards']} rewards"
        )

    except Exception as e:
        print(f"❌ LinUCB test failed: {e}")

    # Test Thompson Sampling
    print("Testing Thompson Sampling bandit...")
    try:
        bandit = ThompsonSampling(d=5, nu=1.0)
        print(f"✅ Thompson Sampling initialized: d={bandit.d}, nu={bandit.nu}")

        context = BanditContext(features=[1.0, 2.0, 3.0, 4.0, 5.0])
        candidates = [{"id": "test", "features": [1.0, 2.0, 3.0, 4.0, 5.0]}]

        action = bandit.select_action(context, candidates)
        print(f"✅ Action selected: {action.id}, confidence={action.confidence:.3f}")

        bandit.update(action, reward=0.9)
        print(f"✅ Bandit updated: total_rewards={bandit.total_rewards}")

    except Exception as e:
        print(f"❌ Thompson Sampling test failed: {e}")

    # Test DPP Selector
    print("Testing DPP Selector...")
    try:
        selector = DPPSelector(lambda_param=1.0, kernel_type="rbf")
        print(
            f"✅ DPP Selector initialized: lambda={selector.lambda_param}, kernel={selector.kernel_type}"
        )

        # Create test items
        items = []
        for i in range(5):
            item = DiversityItem(
                id=f"item_{i}",
                features=[float(i), float(i + 1), float(i + 2)],
                diversity_key=f"key_{i % 2}",
                metadata={"test": f"item_{i}"},
            )
            items.append(item)

        selection = selector.select_diverse_items(items, k=3)
        print(
            f"✅ DPP selection: {len(selection.selected_items)} items, diversity_score={selection.diversity_score:.3f}"
        )

        stats = selector.get_statistics()
        print(
            f"✅ DPP statistics: {stats['total_selections']} selections, avg_diversity={stats['average_diversity_score']:.3f}"
        )

    except Exception as e:
        print(f"❌ DPP Selector test failed: {e}")

    # Test Submodular Selector
    print("Testing Submodular Selector...")
    try:
        selector = SubmodularSelector(alpha=1.0, beta=0.5)
        print(f"✅ Submodular Selector initialized: alpha={selector.alpha}, beta={selector.beta}")

        # Create test items
        items = []
        for i in range(5):
            item = DiversityItem(
                id=f"item_{i}",
                features=[float(i), float(i + 1), float(i + 2)],
                diversity_key=f"key_{i % 2}",
                metadata={"test": f"item_{i}"},
            )
            items.append(item)

        selection = selector.select_diverse_items(items, k=3)
        print(
            f"✅ Submodular selection: {len(selection.selected_items)} items, diversity_score={selection.diversity_score:.3f}"
        )

        stats = selector.get_statistics()
        print(
            f"✅ Submodular statistics: {stats['total_selections']} selections, avg_diversity={stats['average_diversity_score']:.3f}"
        )

    except Exception as e:
        print(f"❌ Submodular Selector test failed: {e}")

    print("✅ Bandit + DPP tests completed!")
