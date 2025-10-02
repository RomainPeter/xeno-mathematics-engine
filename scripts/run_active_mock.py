#!/usr/bin/env python3
"""
Run active mode with mock LLM for CI testing.

This script runs the active gated mode using mock LLM client
to test the full pipeline without network dependencies.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from proofengine.core.llm_client import MockLLMClient
from proofengine.orchestrator.checker import BasicChecker
from proofengine.orchestrator.modes import TwoCategoryOrchestrator
from proofengine.orchestrator.rewriter import PlanRewriter
from proofengine.orchestrator.selector import StrategySelector
from proofengine.orchestrator.strategy_api import StrategyContext, StrategyRegistry
from proofengine.strategies.add_missing_tests import AddMissingTestsStrategy
from proofengine.strategies.changelog_or_block import ChangelogOrBlockStrategy
from proofengine.strategies.decompose_meet import DecomposeMeetStrategy
from proofengine.strategies.guard_before import GuardBeforeStrategy
from proofengine.strategies.pin_dependency import PinDependencyStrategy
from proofengine.strategies.require_semver import RequireSemverStrategy
from proofengine.strategies.retry_with_hardening import RetryWithHardeningStrategy

# Import strategies
from proofengine.strategies.specialize_then_retry import SpecializeThenRetryStrategy


def create_test_context(plan_path: str) -> StrategyContext:
    """Create test context from plan file."""
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    return StrategyContext(
        failreason=plan.get("failreason", "contract.ambiguous_spec"),
        operator=plan.get("operator", "Generalize"),
        plan=plan,
        current_step=plan.get("steps", [{}])[0] if plan.get("steps") else {},
        history=[],
        budgets=plan.get("budgets", {"time_ms": 300000, "audit_cost": 1.0}),
        depth=0,
    )


def setup_orchestrator() -> TwoCategoryOrchestrator:
    """Set up orchestrator with all components."""
    # Create strategy registry
    registry = StrategyRegistry()

    # Register all strategies
    strategies = [
        SpecializeThenRetryStrategy(),
        AddMissingTestsStrategy(),
        RequireSemverStrategy(),
        ChangelogOrBlockStrategy(),
        DecomposeMeetStrategy(),
        RetryWithHardeningStrategy(),
        PinDependencyStrategy(),
        GuardBeforeStrategy(),
    ]

    for strategy in strategies:
        registry.register(strategy)

    # Create components
    checker = BasicChecker()
    rewriter = PlanRewriter(checker)
    llm_client = MockLLMClient()
    selector = StrategySelector(llm_client=llm_client, use_mock=True)

    return TwoCategoryOrchestrator(registry, rewriter, selector)


def run_active_mode_test(plan_path: str) -> dict:
    """Run active mode test and return results."""
    print(f"Running active mode test with plan: {plan_path}")

    # Set up
    orchestrator = setup_orchestrator()
    context = create_test_context(plan_path)

    print(f"Context: failreason={context.failreason}, operator={context.operator}")
    print(f"Plan steps: {len(context.plan.get('steps', []))}")

    # Execute active mode
    result = orchestrator.execute_active_gated_mode(
        context, confidence_threshold=0.6, delta_v_threshold=0.1, max_depth=2
    )

    print(f"Result: success={result.success}")
    if result.success:
        print(f"Applied strategy: {result.applied_strategy}")
        print(f"Confidence: {result.confidence}")
        print(f"Rationale: {result.rationale}")
    else:
        print(f"Error: {result.error}")

    return {
        "success": result.success,
        "applied_strategy": result.applied_strategy,
        "confidence": result.confidence,
        "rationale": result.rationale,
        "error": result.error,
        "selection_result": (result.selection_result.__dict__ if result.selection_result else None),
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run active mode with mock LLM")
    parser.add_argument("--plan", required=True, help="Path to plan JSON file")
    parser.add_argument("--output", help="Output file for results")

    args = parser.parse_args()

    # Check if plan file exists
    if not os.path.exists(args.plan):
        print(f"Error: Plan file not found: {args.plan}")
        sys.exit(1)

    try:
        # Run test
        results = run_active_mode_test(args.plan)

        # Output results
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to: {args.output}")
        else:
            print("\nResults:")
            print(json.dumps(results, indent=2))

        # Exit with appropriate code
        sys.exit(0 if results["success"] else 1)

    except Exception as e:
        print(f"Error running test: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
