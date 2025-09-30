#!/usr/bin/env python3
"""
Tests for policy IDS/CVaR integration
Tests the integration of IDS/CVaR parameters from overrides
"""
import pytest
import json
import tempfile
from pathlib import Path
from orchestrator.policy.select import Selector


class MockBandit:
    """Mock bandit for testing."""

    def __init__(self):
        self.updates = []

    def update(self, cand_id, utility):
        self.updates.append((cand_id, utility))


class MockDiversity:
    """Mock diversity selector for testing."""

    def select(self, candidates):
        return candidates


class TestPolicyIDSVaR:
    """Test IDS/CVaR policy integration."""

    def setup_method(self):
        """Setup test environment."""
        self.bandit = MockBandit()
        self.diversity = MockDiversity()

    def test_default_parameters(self):
        """Test default IDS/CVaR parameters."""
        selector = Selector(self.bandit, self.diversity)

        assert selector.ids_lambda == 0.6, "Default lambda should be 0.6"
        assert selector.cvar_alpha == 0.9, "Default alpha should be 0.9"

    def test_override_parameters(self):
        """Test parameter override from file."""
        # Create temporary overrides file
        overrides = {"ids": {"lambda": 0.8}, "risk_policy": {"cvar_alpha": 0.95}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(overrides, f)
            overrides_file = f.name

        try:
            selector = Selector(self.bandit, self.diversity, overrides_file=overrides_file)

            assert selector.ids_lambda == 0.8, "Should use override lambda"
            assert selector.cvar_alpha == 0.95, "Should use override alpha"

        finally:
            Path(overrides_file).unlink()

    def test_ranking_with_scores(self):
        """Test candidate ranking with IDS scores."""
        candidates = [
            {
                "id": "cand1",
                "V_hat": {"time_ms": 1000},
                "S_hat": 0.8,
                "info_gain": 0.5,
                "var": 0.2,
                "diversity_key": "key1",
            },
            {
                "id": "cand2",
                "V_hat": {"time_ms": 2000},
                "S_hat": 0.9,
                "info_gain": 0.7,
                "var": 0.3,
                "diversity_key": "key2",
            },
        ]

        selector = Selector(self.bandit, self.diversity)
        ranked = selector.rank(candidates)

        assert len(ranked) == 2, "Should return all candidates"
        assert "ids_score" in ranked[0], "Should add IDS scores"
        assert "ids_score" in ranked[1], "Should add IDS scores"

    def test_get_scores(self):
        """Test getting IDS and CVaR scores."""
        candidates = [
            {
                "id": "cand1",
                "V_hat": {"time_ms": 1000},
                "info_gain": 0.5,
                "var": 0.2,
                "reward_samples": [0.8, 0.9],
                "cost_samples": [100, 120],
            }
        ]

        selector = Selector(self.bandit, self.diversity)
        scores = selector.get_scores(candidates)

        assert len(scores) == 1, "Should return scores for all candidates"
        assert "ids_score" in scores[0], "Should include IDS score"
        assert "cvar_score" in scores[0], "Should include CVaR score"
        assert "ids_lambda" in scores[0], "Should include lambda parameter"
        assert "cvar_alpha" in scores[0], "Should include alpha parameter"

    def test_config_retrieval(self):
        """Test configuration retrieval."""
        selector = Selector(self.bandit, self.diversity, ids_lambda=0.7, cvar_alpha=0.85)
        config = selector.get_config()

        assert config["ids_lambda"] == 0.7, "Should return correct lambda"
        assert config["cvar_alpha"] == 0.85, "Should return correct alpha"
        assert "overrides_file" in config, "Should include overrides file info"

    def test_update_with_cvar(self):
        """Test bandit update with CVaR utility."""
        selector = Selector(self.bandit, self.diversity, cvar_alpha=0.9)

        reward_samples = [0.8, 0.9, 0.7]
        cost_samples = [100, 120, 110]

        selector.update("cand1", reward_samples, cost_samples)

        assert len(self.bandit.updates) == 1, "Should record one update"
        cand_id, utility = self.bandit.updates[0]
        assert cand_id == "cand1", "Should update correct candidate"
        assert isinstance(utility, float), "Utility should be numeric"

    def test_override_file_loading(self):
        """Test loading parameters from override file."""
        overrides = {
            "ids": {"lambda": 0.5},
            "risk_policy": {"cvar_alpha": 0.88},
            "calibration": {"best_params": {"lambda": 0.5, "alpha": 0.88}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(overrides, f)
            overrides_file = f.name

        try:
            selector = Selector(self.bandit, self.diversity, overrides_file=overrides_file)

            assert selector.ids_lambda == 0.5, "Should load lambda from overrides"
            assert selector.cvar_alpha == 0.88, "Should load alpha from overrides"

        finally:
            Path(overrides_file).unlink()

    def test_missing_override_file(self):
        """Test behavior with missing override file."""
        selector = Selector(self.bandit, self.diversity, overrides_file="nonexistent.json")

        # Should use defaults
        assert selector.ids_lambda == 0.6, "Should use default lambda"
        assert selector.cvar_alpha == 0.9, "Should use default alpha"

    def test_invalid_override_file(self):
        """Test behavior with invalid override file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            overrides_file = f.name

        try:
            selector = Selector(self.bandit, self.diversity, overrides_file=overrides_file)

            # Should use defaults on error
            assert selector.ids_lambda == 0.6, "Should use default lambda on error"
            assert selector.cvar_alpha == 0.9, "Should use default alpha on error"

        finally:
            Path(overrides_file).unlink()

    def test_partial_overrides(self):
        """Test partial overrides (only some parameters)."""
        overrides = {
            "ids": {"lambda": 0.4}
            # Missing risk_policy section
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(overrides, f)
            overrides_file = f.name

        try:
            selector = Selector(self.bandit, self.diversity, overrides_file=overrides_file)

            assert selector.ids_lambda == 0.4, "Should use override lambda"
            assert selector.cvar_alpha == 0.9, "Should use default alpha"

        finally:
            Path(overrides_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
