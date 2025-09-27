#!/usr/bin/env python3
"""
Benchmark script for 2-category transformations.

Measures performance metrics and compares shadow vs active modes.
"""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from proofengine.orchestrator.modes import TwoCategoryOrchestrator
from proofengine.orchestrator.strategy_api import StrategyContext, StrategyRegistry
from proofengine.orchestrator.rewriter import PlanRewriter
from proofengine.orchestrator.selector import StrategySelector
from proofengine.orchestrator.checker import BasicChecker
from proofengine.core.llm_client import MockLLMClient

# Import strategies
from proofengine.strategies.specialize_then_retry import SpecializeThenRetryStrategy
from proofengine.strategies.add_missing_tests import AddMissingTestsStrategy
from proofengine.strategies.require_semver import RequireSemverStrategy
from proofengine.strategies.changelog_or_block import ChangelogOrBlockStrategy
from proofengine.strategies.decompose_meet import DecomposeMeetStrategy
from proofengine.strategies.retry_with_hardening import RetryWithHardeningStrategy
from proofengine.strategies.pin_dependency import PinDependencyStrategy
from proofengine.strategies.guard_before import GuardBeforeStrategy


class BenchmarkSuite:
    """Benchmark suite for 2-category transformations."""

    def __init__(self, use_mock: bool = True):
        """Initialize benchmark suite."""
        self.use_mock = use_mock
        self.orchestrator = self._setup_orchestrator()
        self.results = []

    def _setup_orchestrator(self) -> TwoCategoryOrchestrator:
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
        llm_client = MockLLMClient() if self.use_mock else None
        selector = StrategySelector(llm_client=llm_client, use_mock=self.use_mock)

        return TwoCategoryOrchestrator(registry, rewriter, selector)

    def create_test_context(self, plan: Dict[str, Any]) -> StrategyContext:
        """Create test context from plan."""
        return StrategyContext(
            failreason=plan.get("failreason", "contract.ambiguous_spec"),
            operator=plan.get("operator", "Generalize"),
            plan=plan,
            current_step=plan.get("steps", [{}])[0] if plan.get("steps") else {},
            history=[],
            budgets=plan.get("budgets", {"time_ms": 300000, "audit_cost": 1.0}),
            depth=0,
        )

    def benchmark_shadow_mode(self, context: StrategyContext) -> Dict[str, Any]:
        """Benchmark shadow mode execution."""
        start_time = time.time()

        report = self.orchestrator.execute_shadow_mode(context)

        end_time = time.time()

        return {
            "mode": "shadow",
            "execution_time_ms": (end_time - start_time) * 1000,
            "proposals_count": len(report.proposals),
            "applicable_strategies": report.applicable_strategies,
            "total_strategies": report.total_strategies_evaluated,
            "success_rate": report.success_rate,
            "timestamp": report.timestamp,
        }

    def benchmark_active_mode(self, context: StrategyContext) -> Dict[str, Any]:
        """Benchmark active mode execution."""
        start_time = time.time()

        result = self.orchestrator.execute_active_gated_mode(
            context, confidence_threshold=0.6, delta_v_threshold=0.1, max_depth=2
        )

        end_time = time.time()

        return {
            "mode": "active",
            "execution_time_ms": (end_time - start_time) * 1000,
            "success": result.success,
            "applied_strategy": result.applied_strategy,
            "confidence": result.confidence,
            "error": result.error,
            "selection_result": (
                result.selection_result.__dict__ if result.selection_result else None
            ),
        }

    def run_suite(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run benchmark suite on test cases."""
        print(f"Running benchmark suite with {len(test_cases)} test cases")
        print(f"Mock mode: {self.use_mock}")

        shadow_results = []
        active_results = []

        for i, test_case in enumerate(test_cases):
            print(
                f"\nTest case {i+1}/{len(test_cases)}: {test_case.get('name', 'unnamed')}"
            )

            context = self.create_test_context(test_case)

            # Benchmark shadow mode
            print("  Running shadow mode...")
            shadow_result = self.benchmark_shadow_mode(context)
            shadow_result["test_case"] = test_case.get("name", f"test_{i+1}")
            shadow_results.append(shadow_result)

            # Benchmark active mode
            print("  Running active mode...")
            active_result = self.benchmark_active_mode(context)
            active_result["test_case"] = test_case.get("name", f"test_{i+1}")
            active_results.append(active_result)

        # Calculate aggregate metrics
        shadow_metrics = self._calculate_metrics(shadow_results)
        active_metrics = self._calculate_metrics(active_results)

        # Calculate improvement metrics
        improvement = self._calculate_improvement(shadow_metrics, active_metrics)

        return {
            "shadow_mode": shadow_metrics,
            "active_mode": active_metrics,
            "improvement": improvement,
            "test_cases": len(test_cases),
            "mock_mode": self.use_mock,
        }

    def _calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate metrics from results."""
        if not results:
            return {}

        execution_times = [r["execution_time_ms"] for r in results]
        success_rates = [
            r.get("success_rate", 0) for r in results if "success_rate" in r
        ]
        success_counts = [r.get("success", False) for r in results if "success" in r]

        return {
            "avg_execution_time_ms": sum(execution_times) / len(execution_times),
            "min_execution_time_ms": min(execution_times),
            "max_execution_time_ms": max(execution_times),
            "avg_success_rate": (
                sum(success_rates) / len(success_rates) if success_rates else 0
            ),
            "success_count": sum(success_counts) if success_counts else 0,
            "total_tests": len(results),
        }

    def _calculate_improvement(
        self, shadow_metrics: Dict[str, Any], active_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate improvement metrics between shadow and active modes."""
        if not shadow_metrics or not active_metrics:
            return {}

        # Calculate accept rate improvement
        shadow_accept_rate = shadow_metrics.get("avg_success_rate", 0)
        active_accept_rate = active_metrics.get(
            "success_count", 0
        ) / active_metrics.get("total_tests", 1)
        accept_rate_improvement = (active_accept_rate - shadow_accept_rate) * 100

        # Calculate execution time overhead
        shadow_time = shadow_metrics.get("avg_execution_time_ms", 0)
        active_time = active_metrics.get("avg_execution_time_ms", 0)
        time_overhead = (
            ((active_time - shadow_time) / shadow_time * 100) if shadow_time > 0 else 0
        )

        return {
            "accept_rate_improvement_pts": accept_rate_improvement,
            "time_overhead_percent": time_overhead,
            "shadow_accept_rate": shadow_accept_rate,
            "active_accept_rate": active_accept_rate,
        }


def load_test_suite(suite_name: str) -> List[Dict[str, Any]]:
    """Load test suite from corpus."""
    suite_path = Path(f"corpus/s2/{suite_name}")

    if not suite_path.exists():
        print(f"Warning: Test suite {suite_name} not found, using mock data")
        return create_mock_test_suite()

    test_cases = []
    for plan_file in suite_path.glob("*.json"):
        with open(plan_file, "r", encoding="utf-8") as f:
            plan = json.load(f)
            test_cases.append({"name": plan_file.stem, **plan})

    return test_cases


def create_mock_test_suite() -> List[Dict[str, Any]]:
    """Create mock test suite for benchmarking."""
    return [
        {
            "name": "api_break_mock",
            "failreason": "api.semver_missing",
            "operator": "Generalize",
            "steps": [{"id": "step1", "operator": "Meet"}],
            "goal": "Test API breaking change",
            "budgets": {"time_ms": 300000, "audit_cost": 1.0},
        },
        {
            "name": "typosquat_mock",
            "failreason": "policy.dependency_pin_required",
            "operator": "InstallDependency",
            "steps": [
                {
                    "id": "step1",
                    "operator": "InstallDependency",
                    "params": {"package": "requests"},
                }
            ],
            "goal": "Test dependency pinning",
            "budgets": {"time_ms": 300000, "audit_cost": 1.0},
        },
        {
            "name": "secret_egress_mock",
            "failreason": "policy.secret",
            "operator": "DataProcessing",
            "steps": [
                {
                    "id": "step1",
                    "operator": "DataProcessing",
                    "params": {"data": "sensitive"},
                }
            ],
            "goal": "Test secret protection",
            "budgets": {"time_ms": 300000, "audit_cost": 1.0},
        },
    ]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark 2-category transformations")
    parser.add_argument("--suite", default="s2-sample", help="Test suite name")
    parser.add_argument(
        "--mode",
        choices=["shadow", "active", "both"],
        default="both",
        help="Benchmark mode",
    )
    parser.add_argument("--mock", action="store_true", help="Use mock LLM client")
    parser.add_argument("--output", help="Output file for results")

    args = parser.parse_args()

    try:
        # Load test suite
        test_cases = load_test_suite(args.suite)
        print(f"Loaded {len(test_cases)} test cases from suite '{args.suite}'")

        # Run benchmark
        suite = BenchmarkSuite(use_mock=args.mock)
        results = suite.run_suite(test_cases)

        # Print results
        print("\n" + "=" * 50)
        print("BENCHMARK RESULTS")
        print("=" * 50)

        if "shadow_mode" in results:
            shadow = results["shadow_mode"]
            print("\nShadow Mode:")
            print(
                f"  Avg execution time: {shadow.get('avg_execution_time_ms', 0):.2f}ms"
            )
            print(f"  Avg success rate: {shadow.get('avg_success_rate', 0):.2%}")

        if "active_mode" in results:
            active = results["active_mode"]
            print("\nActive Mode:")
            print(
                f"  Avg execution time: {active.get('avg_execution_time_ms', 0):.2f}ms"
            )
            print(
                f"  Success count: {active.get('success_count', 0)}/{active.get('total_tests', 0)}"
            )

        if "improvement" in results:
            improvement = results["improvement"]
            print("\nImprovement:")
            print(
                f"  Accept rate improvement: {improvement.get('accept_rate_improvement_pts', 0):+.1f} pts"
            )
            print(
                f"  Time overhead: {improvement.get('time_overhead_percent', 0):+.1f}%"
            )

        # Save results
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {args.output}")

        # Check if benchmarks meet criteria
        if "improvement" in results:
            improvement = results["improvement"]
            accept_rate_improvement = improvement.get("accept_rate_improvement_pts", 0)
            time_overhead = improvement.get("time_overhead_percent", 0)

            print("\nBenchmark Criteria:")
            print(
                f"  Accept rate improvement ≥ +8 pts: {'✓' if accept_rate_improvement >= 8 else '✗'} ({accept_rate_improvement:+.1f} pts)"
            )
            print(
                f"  Time overhead ≤ +15%: {'✓' if time_overhead <= 15 else '✗'} ({time_overhead:+.1f}%)"
            )

            if accept_rate_improvement >= 8 and time_overhead <= 15:
                print("\n🎉 All benchmark criteria met!")
                sys.exit(0)
            else:
                print("\n❌ Some benchmark criteria not met")
                sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"Error running benchmark: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
