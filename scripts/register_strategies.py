#!/usr/bin/env python3
"""
Register all available strategies.
"""

from proofengine.orchestrator.strategy_api import StrategyRegistry
from proofengine.strategies.require_semver import RequireSemverStrategy
from proofengine.strategies.changelog_or_block import ChangelogOrBlockStrategy
from proofengine.strategies.pin_dependency import PinDependencyStrategy
from proofengine.strategies.guard_before import GuardBeforeStrategy


def register_all_strategies() -> StrategyRegistry:
    """Register all available strategies."""
    registry = StrategyRegistry()

    # Register existing strategies
    registry.register(RequireSemverStrategy())
    registry.register(ChangelogOrBlockStrategy())
    registry.register(PinDependencyStrategy())
    registry.register(GuardBeforeStrategy())

    return registry


if __name__ == "__main__":
    registry = register_all_strategies()
    print(f"Registered {len(registry.get_all())} strategies:")
    for strategy in registry.get_all():
        print(f"  - {strategy.id}: {strategy.trigger_codes}")
