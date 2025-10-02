"""
Tests for the strategy catalog.
Tests golden cases for each strategy.
"""

from proofengine.orchestrator.strategy_api import StrategyContext
from proofengine.strategies import (
    AddMissingTestsStrategy,
    ChangelogOrBlockStrategy,
    DecomposeMeetStrategy,
    RequireSemverStrategy,
    RetryWithHardeningStrategy,
    SpecializeThenRetryStrategy,
)


class TestSpecializeThenRetryStrategy:
    """Test SpecializeThenRetry strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = SpecializeThenRetryStrategy()

    def test_can_apply_ambiguous_spec(self):
        """Test that strategy can be applied to ambiguous spec."""
        context = StrategyContext(
            failreason="contract.ambiguous_spec",
            operator="Generalize",
            plan={"steps": [{"id": "step1", "operator": "Generalize"}]},
            current_step={"id": "step1", "operator": "Generalize"},
            history=[],
            budgets={},
        )

        assert self.strategy.can_apply(context)

    def test_cannot_apply_wrong_failreason(self):
        """Test that strategy cannot be applied to wrong failreason."""
        context = StrategyContext(
            failreason="test_failure",
            operator="Generalize",
            plan={"steps": []},
            current_step={},
            history=[],
            budgets={},
        )

        assert not self.strategy.can_apply(context)

    def test_create_rewrite_plan(self):
        """Test rewrite plan creation."""
        context = StrategyContext(
            failreason="contract.ambiguous_spec",
            operator="Generalize",
            plan={"steps": [{"id": "step1", "operator": "Generalize"}]},
            current_step={"id": "step1", "operator": "Generalize"},
            history=[],
            budgets={},
        )

        rewrite_plan = self.strategy.create_rewrite_plan(context)

        assert rewrite_plan.operation.value == "insert"
        assert rewrite_plan.at == "before:current"
        assert len(rewrite_plan.steps) == 1
        assert rewrite_plan.steps[0]["operator"] == "Specialize"


class TestAddMissingTestsStrategy:
    """Test AddMissingTests strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = AddMissingTestsStrategy()

    def test_can_apply_missing_tests(self):
        """Test that strategy can be applied to missing tests."""
        context = StrategyContext(
            failreason="coverage.missing_tests",
            operator="Verify",
            plan={"steps": [{"id": "verify1", "operator": "Verify"}]},
            current_step={"id": "verify1", "operator": "Verify"},
            history=[],
            budgets={},
        )

        assert self.strategy.can_apply(context)

    def test_create_rewrite_plan(self):
        """Test rewrite plan creation."""
        context = StrategyContext(
            failreason="coverage.missing_tests",
            operator="Verify",
            plan={"steps": [{"id": "verify1", "operator": "Verify"}]},
            current_step={"id": "verify1", "operator": "Verify"},
            history=[],
            budgets={},
        )

        rewrite_plan = self.strategy.create_rewrite_plan(context)

        assert rewrite_plan.operation.value == "insert"
        assert rewrite_plan.at == "before:Verify"
        assert len(rewrite_plan.steps) == 1
        assert rewrite_plan.steps[0]["operator"] == "Meet"


class TestRequireSemverStrategy:
    """Test RequireSemver strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = RequireSemverStrategy()

    def test_can_apply_semver_missing(self):
        """Test that strategy can be applied to semver missing."""
        context = StrategyContext(
            failreason="api.semver_missing",
            operator="Normalize",
            plan={"steps": [{"id": "norm1", "operator": "Normalize"}]},
            current_step={"id": "norm1", "operator": "Normalize"},
            history=[],
            budgets={},
        )

        assert self.strategy.can_apply(context)

    def test_create_rewrite_plan(self):
        """Test rewrite plan creation."""
        context = StrategyContext(
            failreason="api.semver_missing",
            operator="Normalize",
            plan={"steps": [{"id": "norm1", "operator": "Normalize"}]},
            current_step={"id": "norm1", "operator": "Normalize"},
            history=[],
            budgets={},
        )

        rewrite_plan = self.strategy.create_rewrite_plan(context)

        assert rewrite_plan.operation.value == "insert"
        assert rewrite_plan.at == "before:current"
        assert len(rewrite_plan.steps) == 1
        assert rewrite_plan.steps[0]["operator"] == "Normalize"
        assert "semver" in rewrite_plan.steps[0]["params"]["target"]


class TestChangelogOrBlockStrategy:
    """Test ChangelogOrBlock strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = ChangelogOrBlockStrategy()

    def test_can_apply_changelog_missing(self):
        """Test that strategy can be applied to changelog missing."""
        context = StrategyContext(
            failreason="api.changelog_missing",
            operator="Normalize",
            plan={"steps": [{"id": "norm1", "operator": "Normalize"}]},
            current_step={"id": "norm1", "operator": "Normalize"},
            history=[],
            budgets={},
        )

        assert self.strategy.can_apply(context)

    def test_create_rewrite_plan(self):
        """Test rewrite plan creation."""
        context = StrategyContext(
            failreason="api.changelog_missing",
            operator="Normalize",
            plan={"steps": [{"id": "norm1", "operator": "Normalize"}]},
            current_step={"id": "norm1", "operator": "Normalize"},
            history=[],
            budgets={},
        )

        rewrite_plan = self.strategy.create_rewrite_plan(context)

        assert rewrite_plan.operation.value == "insert"
        assert rewrite_plan.at == "before:current"
        assert len(rewrite_plan.steps) == 1
        assert rewrite_plan.steps[0]["operator"] == "Normalize"
        assert "changelog" in rewrite_plan.steps[0]["params"]["target"]


class TestDecomposeMeetStrategy:
    """Test DecomposeMeet strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = DecomposeMeetStrategy()

    def test_can_apply_complex_hypothesis(self):
        """Test that strategy can be applied to complex hypothesis."""
        context = StrategyContext(
            failreason="runner.test_failure",
            operator="Meet",
            plan={"steps": []},
            current_step={
                "id": "meet1",
                "operator": "Meet",
                "params": {"hypothesis": "A ∧ B"},
            },
            history=[],
            budgets={},
        )

        assert self.strategy.can_apply(context)

    def test_cannot_apply_simple_hypothesis(self):
        """Test that strategy cannot be applied to simple hypothesis."""
        context = StrategyContext(
            failreason="runner.test_failure",
            operator="Meet",
            plan={"steps": []},
            current_step={
                "id": "meet1",
                "operator": "Meet",
                "params": {"hypothesis": "Simple hypothesis"},
            },
            history=[],
            budgets={},
        )

        assert not self.strategy.can_apply(context)

    def test_decompose_hypothesis(self):
        """Test hypothesis decomposition."""
        hypothesis = "A ∧ B"
        decomposed = self.strategy._decompose_hypothesis(hypothesis)

        assert len(decomposed) == 2
        assert "A" in decomposed[0]
        assert "B" in decomposed[1]

    def test_create_rewrite_plan(self):
        """Test rewrite plan creation."""
        context = StrategyContext(
            failreason="runner.test_failure",
            operator="Meet",
            plan={"steps": []},
            current_step={
                "id": "meet1",
                "operator": "Meet",
                "params": {"hypothesis": "A ∧ B"},
            },
            history=[],
            budgets={},
        )

        rewrite_plan = self.strategy.create_rewrite_plan(context)

        assert rewrite_plan.operation.value == "replace"
        assert rewrite_plan.at == "meet1"


class TestRetryWithHardeningStrategy:
    """Test RetryWithHardening strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = RetryWithHardeningStrategy()

    def test_can_apply_flaky_test(self):
        """Test that strategy can be applied to flaky test."""
        context = StrategyContext(
            failreason="nondet.flaky_test",
            operator="Meet",
            plan={"steps": [{"id": "meet1", "operator": "Meet"}]},
            current_step={"id": "meet1", "operator": "Meet"},
            history=[],
            budgets={},
        )

        assert self.strategy.can_apply(context)

    def test_create_rewrite_plan(self):
        """Test rewrite plan creation."""
        context = StrategyContext(
            failreason="nondet.flaky_test",
            operator="Meet",
            plan={"steps": [{"id": "meet1", "operator": "Meet"}]},
            current_step={"id": "meet1", "operator": "Meet"},
            history=[],
            budgets={},
        )

        rewrite_plan = self.strategy.create_rewrite_plan(context)

        assert rewrite_plan.operation.value == "insert"
        assert rewrite_plan.at == "before:current"
        assert len(rewrite_plan.steps) == 1
        assert rewrite_plan.steps[0]["operator"] == "Normalize"
        assert rewrite_plan.steps[0]["params"]["fix_seed"] is True


class TestStrategyGoldenCases:
    """Test golden cases for all strategies."""

    def test_all_strategies_registered(self):
        """Test that all strategies are properly registered."""
        strategies = [
            SpecializeThenRetryStrategy(),
            AddMissingTestsStrategy(),
            RequireSemverStrategy(),
            ChangelogOrBlockStrategy(),
            DecomposeMeetStrategy(),
            RetryWithHardeningStrategy(),
        ]

        assert len(strategies) == 6

        for strategy in strategies:
            assert strategy.id is not None
            assert len(strategy.trigger_codes) > 0
            assert len(strategy.expected_outcomes) > 0
            assert strategy.guards.max_depth <= 2
            assert strategy.guards.max_rewrites_per_fr <= 1
