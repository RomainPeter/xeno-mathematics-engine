"""
Test script for strategy expected-fail cases.
Validates that strategies work correctly in red/green scenarios.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path setup
from proofengine.strategies import (
    SpecializeThenRetryStrategy,
    AddMissingTestsStrategy,
    RequireSemverStrategy,
    ChangelogOrBlockStrategy,
    DecomposeMeetStrategy,
    RetryWithHardeningStrategy,
)
from proofengine.orchestrator.strategy_api import StrategyContext


class StrategyExpectedFailTester:
    """Test expected-fail cases for strategies."""

    def __init__(self):
        self.strategies = {
            "specialize_then_retry": SpecializeThenRetryStrategy(),
            "add_missing_tests": AddMissingTestsStrategy(),
            "require_semver": RequireSemverStrategy(),
            "changelog_or_block": ChangelogOrBlockStrategy(),
            "decompose_meet": DecomposeMeetStrategy(),
            "retry_with_hardening": RetryWithHardeningStrategy(),
        }

    def test_red_case(self, test_file: str) -> Dict[str, Any]:
        """Test red case (before strategy application)."""
        with open(test_file, "r", encoding="utf-8") as f:
            test_data = json.load(f)

        input_data = test_data["input"]

        # Create context
        context = StrategyContext(
            failreason=input_data["failreason"]["code"],
            operator=input_data["context"]["operator"],
            plan=input_data["plan"],
            current_step=input_data["context"]["current_step"],
            history=input_data["context"]["history"],
            budgets=input_data["context"]["budgets"],
        )

        # Test strategy application
        strategy_name = test_data["strategy_application"]["strategy_id"]
        strategy = self.strategies[strategy_name]

        can_apply = strategy.can_apply(context)
        success_prob = strategy.estimate_success_probability(context)

        return {
            "test_case": test_data["test_case"],
            "strategy": strategy_name,
            "can_apply": can_apply,
            "success_probability": success_prob,
            "expected_can_apply": test_data["strategy_application"]["can_apply"],
            "expected_success_prob": test_data["strategy_application"][
                "success_probability"
            ],
            "passed": (
                can_apply == test_data["strategy_application"]["can_apply"]
                and abs(
                    success_prob
                    - test_data["strategy_application"]["success_probability"]
                )
                < 0.1
            ),
        }

    def test_green_case(self, test_file: str) -> Dict[str, Any]:
        """Test green case (after strategy application)."""
        with open(test_file, "r", encoding="utf-8") as f:
            test_data = json.load(f)

        input_data = test_data["input"]
        expected_after = test_data["expected_after"]

        # Create context
        StrategyContext(
            failreason=input_data["failreason"]["code"],
            operator=input_data["context"]["operator"],
            plan=input_data["plan"],
            current_step=input_data["context"]["current_step"],
            history=input_data["context"]["history"],
            budgets=input_data["context"]["budgets"],
        )

        # Test that the plan should now succeed
        # This is a simplified check - in reality, we'd run the plan
        plan_steps = input_data["plan"]["steps"]
        has_specialization = any(
            step.get("operator") == "Specialize" for step in plan_steps
        )

        return {
            "test_case": test_data["test_case"],
            "has_specialization": has_specialization,
            "expected_success": expected_after["success"],
            "passed": has_specialization == expected_after["success"],
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all expected-fail tests."""
        test_dir = project_root / "examples" / "expected_fail" / "strategies"

        results = {
            "red_cases": [],
            "green_cases": [],
            "summary": {},
        }

        # Test red cases
        red_files = list(test_dir.glob("*_red.json"))
        for red_file in red_files:
            try:
                result = self.test_red_case(str(red_file))
                results["red_cases"].append(result)
            except Exception as e:
                results["red_cases"].append(
                    {
                        "test_case": red_file.stem,
                        "error": str(e),
                        "passed": False,
                    }
                )

        # Test green cases
        green_files = list(test_dir.glob("*_green.json"))
        for green_file in green_files:
            try:
                result = self.test_green_case(str(green_file))
                results["green_cases"].append(result)
            except Exception as e:
                results["green_cases"].append(
                    {
                        "test_case": green_file.stem,
                        "error": str(e),
                        "passed": False,
                    }
                )

        # Calculate summary
        red_passed = sum(1 for r in results["red_cases"] if r.get("passed", False))
        green_passed = sum(1 for r in results["green_cases"] if r.get("passed", False))

        results["summary"] = {
            "red_cases_total": len(results["red_cases"]),
            "red_cases_passed": red_passed,
            "green_cases_total": len(results["green_cases"]),
            "green_cases_passed": green_passed,
            "overall_success": (red_passed + green_passed)
            / (len(results["red_cases"]) + len(results["green_cases"])),
        }

        return results


def main():
    """Main function to run expected-fail tests."""
    tester = StrategyExpectedFailTester()
    results = tester.run_all_tests()

    print("Strategy Expected-Fail Test Results")
    print("=" * 50)

    print(
        f"Red Cases: {results['summary']['red_cases_passed']}/{results['summary']['red_cases_total']}"
    )
    print(
        f"Green Cases: {results['summary']['green_cases_passed']}/{results['summary']['green_cases_total']}"
    )
    print(f"Overall Success: {results['summary']['overall_success']:.1%}")

    print("\nRed Case Details:")
    for result in results["red_cases"]:
        status = "✓" if result.get("passed", False) else "✗"
        print(f"  {status} {result['test_case']}: {result.get('error', 'OK')}")

    print("\nGreen Case Details:")
    for result in results["green_cases"]:
        status = "✓" if result.get("passed", False) else "✗"
        print(f"  {status} {result['test_case']}: {result.get('error', 'OK')}")

    # Save results
    output_file = project_root / "out" / "strategy_expected_fail_results.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return results["summary"]["overall_success"] > 0.8


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
