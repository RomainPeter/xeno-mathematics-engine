"""
Tests for LLM-based strategy selector.

Tests auto-consistency, scoring, fallback behavior, and caching.
"""

import pytest
from unittest.mock import Mock, patch
from proofengine.orchestrator.selector import StrategySelector, SelectionResult
from proofengine.orchestrator.strategy_api import StrategyContext, Guards
from proofengine.core.llm_client import LLMClient, LLMRequest, LLMResponse


class TestStrategySelector:
    """Test strategy selector functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_client = Mock(spec=LLMClient)
        self.selector = StrategySelector(llm_client=self.mock_llm_client)

        # Mock strategy
        self.mock_strategy = Mock()
        self.mock_strategy.id = "test_strategy"
        self.mock_strategy.guards = Guards(max_depth=2, max_rewrites_per_fr=1)
        self.mock_strategy.expected_outcomes = ["pass_or_block"]

        # Mock context
        self.context = StrategyContext(
            failreason="contract.ambiguous_spec",
            operator="Generalize",
            plan={"steps": [{"id": "step1", "operator": "Meet"}], "goal": "Test goal"},
            current_step={"id": "step1", "operator": "Meet"},
            history=[],
            budgets={"time_ms": 1000, "audit_cost": 10.0},
            depth=0,
        )

    def test_selector_initialization(self):
        """Test selector initialization."""
        assert self.selector.llm_client == self.mock_llm_client
        assert "contract.ambiguous_spec" in self.selector.strategy_whitelist
        assert (
            "specialize_then_retry"
            in self.selector.strategy_whitelist["contract.ambiguous_spec"]
        )

    def test_filter_by_whitelist(self):
        """Test strategy filtering by whitelist."""
        strategies = [self.mock_strategy]

        # Test with matching failreason
        filtered = self.selector._filter_by_whitelist(
            strategies, "contract.ambiguous_spec"
        )
        assert len(filtered) == 1

        # Test with non-matching failreason
        filtered = self.selector._filter_by_whitelist(strategies, "unknown.failure")
        assert len(filtered) == 0

    def test_create_selection_prompt(self):
        """Test prompt creation for LLM."""
        strategies = [self.mock_strategy]
        prompt = self.selector._create_selection_prompt(self.context, strategies)

        assert "contract.ambiguous_spec" in prompt
        assert "Generalize" in prompt
        assert "test_strategy" in prompt
        assert "JSON" in prompt

    def test_parse_llm_response_valid(self):
        """Test parsing valid LLM response."""
        valid_response = """
        {
            "selected_strategy": {
                "id": "test_strategy",
                "score": 0.85,
                "confidence": 0.9,
                "reason": "Good fit for this context",
                "expected_gain": 0.7,
                "risk_assessment": "low"
            },
            "alternative_strategies": [],
            "reasoning": {
                "analysis": "Strategy fits well",
                "constraints_considered": ["budget", "depth"]
            }
        }
        """

        result = self.selector._parse_llm_response(valid_response)
        assert result["selected_strategy"]["id"] == "test_strategy"
        assert result["selected_strategy"]["score"] == 0.85

    def test_parse_llm_response_invalid(self):
        """Test parsing invalid LLM response."""
        invalid_response = "This is not JSON"

        with pytest.raises(ValueError, match="Invalid LLM response format"):
            self.selector._parse_llm_response(invalid_response)

    def test_apply_scoring(self):
        """Test multi-criteria scoring application."""
        selection = {
            "selected_strategy": {
                "id": "test_strategy",
                "score": 0.8,
                "confidence": 0.9,
                "reason": "Good fit",
                "expected_gain": 0.7,
                "risk_assessment": "low",
            },
            "alternative_strategies": [],
            "reasoning": {"analysis": "Good strategy"},
        }

        strategies = [self.mock_strategy]
        result = self.selector._apply_scoring(selection, self.context, strategies)

        assert isinstance(result, SelectionResult)
        assert result.strategy_id == "test_strategy"
        assert 0.0 <= result.score <= 1.0
        assert result.confidence == 0.9

    def test_calculate_scores(self):
        """Test individual scoring criteria calculation."""
        selected = {"id": "test_strategy", "score": 0.8, "expected_gain": 0.7}

        scores = self.selector._calculate_scores(
            selected, self.mock_strategy, self.context
        )

        assert "validity" in scores
        assert "cost_efficiency" in scores
        assert "historical_success" in scores
        assert "output_size" in scores
        assert "entropy" in scores

        # All scores should be in [0, 1]
        for score in scores.values():
            assert 0.0 <= score <= 1.0

    def test_estimate_strategy_cost(self):
        """Test strategy cost estimation."""
        cost = self.selector._estimate_strategy_cost(self.mock_strategy, self.context)
        assert cost > 0.0

    def test_get_historical_success_rate(self):
        """Test historical success rate lookup."""
        rate = self.selector._get_historical_success_rate(
            "specialize_then_retry", "contract.ambiguous_spec"
        )
        assert 0.0 <= rate <= 1.0

    def test_fallback_selection(self):
        """Test deterministic fallback selection."""
        strategies = [self.mock_strategy]
        result = self.selector._fallback_selection(self.context, strategies)

        assert isinstance(result, SelectionResult)
        assert result.strategy_id == "test_strategy"
        assert result.score == 0.6  # Medium confidence
        assert "fallback" in result.reason

    def test_fallback_selection_no_strategies(self):
        """Test fallback with no available strategies."""
        with pytest.raises(ValueError, match="No applicable strategies found"):
            self.selector._fallback_selection(self.context, [])

    def test_select_strategy_success(self):
        """Test successful strategy selection."""
        # Mock LLM response
        mock_response = LLMResponse(
            content='{"selected_strategy": {"id": "test_strategy", "score": 0.8, "confidence": 0.9, "reason": "Good fit", "expected_gain": 0.7, "risk_assessment": "low"}, "alternative_strategies": [], "reasoning": {"analysis": "Good strategy"}}',
            model="kimi/kimi-2",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            latency_ms=100,
        )

        self.mock_llm_client.generate.return_value = mock_response

        strategies = [self.mock_strategy]
        result = self.selector.select_strategy(self.context, strategies)

        assert isinstance(result, SelectionResult)
        assert result.strategy_id == "test_strategy"
        self.mock_llm_client.generate.assert_called_once()

    def test_select_strategy_llm_failure(self):
        """Test strategy selection when LLM fails."""
        self.mock_llm_client.generate.side_effect = Exception("LLM API error")

        strategies = [self.mock_strategy]
        result = self.selector.select_strategy(self.context, strategies)

        # Should fallback to deterministic selection
        assert isinstance(result, SelectionResult)
        assert result.strategy_id == "test_strategy"
        assert "fallback" in result.reason

    def test_select_strategy_no_applicable(self):
        """Test selection with no applicable strategies."""
        # Filter out all strategies
        with patch.object(self.selector, "_filter_by_whitelist", return_value=[]):
            strategies = [self.mock_strategy]
            result = self.selector.select_strategy(self.context, strategies)

            # Should use fallback
            assert isinstance(result, SelectionResult)

    def test_scoring_weights(self):
        """Test that scoring weights sum to 1.0."""
        total_weight = sum(self.selector.scoring_weights.values())
        assert abs(total_weight - 1.0) < 0.001

    def test_whitelist_coverage(self):
        """Test that whitelist covers expected failreasons."""
        expected_failreasons = [
            "contract.ambiguous_spec",
            "coverage.missing_test",
            "api.semver_missing",
            "api.changelog_missing",
            "runner.test_failure",
            "nondet.flaky_test",
            "policy.dependency_pin_required",
            "policy.secret",
            "policy.egress",
        ]

        for failreason in expected_failreasons:
            assert failreason in self.selector.strategy_whitelist
            assert len(self.selector.strategy_whitelist[failreason]) > 0


class TestMockLLMClient:
    """Test mock LLM client functionality."""

    def test_mock_client_initialization(self):
        """Test mock client initialization."""
        from proofengine.core.llm_client import MockLLMClient

        client = MockLLMClient()
        assert client.config is not None
        assert "model" in client.config

    def test_mock_client_generate(self):
        """Test mock client response generation."""
        from proofengine.core.llm_client import MockLLMClient

        client = MockLLMClient()
        request = LLMRequest(
            prompt="Select strategy for contract.ambiguous_spec", model="kimi/kimi-2"
        )

        response = client.generate(request)

        assert isinstance(response, LLMResponse)
        assert response.model == "kimi/kimi-2"
        assert response.latency_ms == 100
        assert not response.cache_hit

    def test_mock_client_strategy_prompt(self):
        """Test mock client with strategy-related prompt."""
        from proofengine.core.llm_client import MockLLMClient

        client = MockLLMClient()
        request = LLMRequest(prompt="strategy selection for test", model="kimi/kimi-2")

        response = client.generate(request)

        # Should return strategy-related JSON
        assert "strategy_id" in response.content
        assert "specialize_then_retry" in response.content
