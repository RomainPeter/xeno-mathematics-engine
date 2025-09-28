#!/usr/bin/env python3
"""
Benchmark script for S2 vendors scenarios
"""

import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any


class S2VendorsBenchmark:
    """Benchmark for S2 vendors scenarios"""

    def __init__(self):
        self.results = []
        self.scenarios = ["api-break", "typosquat-cve", "secret-egress"]

    def run_scenario(self, scenario: str, mode: str = "both") -> Dict[str, Any]:
        """Run a single scenario"""
        print(f"Running scenario: {scenario}")

        start_time = time.time()

        # Load scenario data
        scenario_dir = Path(f"corpus/s2/vendors/{scenario}")
        plan_file = scenario_dir / "plan.json"

        if not plan_file.exists():
            raise FileNotFoundError(f"Plan file not found: {plan_file}")

        with open(plan_file) as f:
            plan_data = json.load(f)

        # Simulate shadow mode
        shadow_start = time.time()
        shadow_success = self._simulate_shadow_mode(plan_data)
        shadow_time = (time.time() - shadow_start) * 1000  # ms

        # Simulate active mode
        active_start = time.time()
        active_success = self._simulate_active_mode(plan_data, scenario)
        active_time = (time.time() - active_start) * 1000  # ms

        total_time = (time.time() - start_time) * 1000  # ms

        result = {
            "scenario": scenario,
            "shadow_mode": {"success": shadow_success, "time_ms": shadow_time},
            "active_mode": {"success": active_success, "time_ms": active_time},
            "total_time_ms": total_time,
            "improvement": active_success - shadow_success,
        }

        self.results.append(result)
        return result

    def _simulate_shadow_mode(self, plan_data: Dict[str, Any]) -> bool:
        """Simulate shadow mode (proposals only)"""
        # Shadow mode just proposes strategies
        return True  # Always succeeds in proposing

    def _simulate_active_mode(self, plan_data: Dict[str, Any], scenario: str) -> bool:
        """Simulate active mode (actual rewrite)"""
        # Simulate the rewrite process
        if scenario == "api-break":
            # Simulate require_semver + changelog_or_block
            return True
        elif scenario == "typosquat-cve":
            # Simulate pin_dependency
            return True
        elif scenario == "secret-egress":
            # Simulate guard_before
            return True

        return False

    def run_benchmark(self, mode: str = "both") -> Dict[str, Any]:
        """Run full benchmark"""
        print("Starting S2 vendors benchmark...")

        for scenario in self.scenarios:
            try:
                self.run_scenario(scenario, mode)
            except Exception as e:
                print(f"Error in scenario {scenario}: {e}")
                self.results.append(
                    {
                        "scenario": scenario,
                        "error": str(e),
                        "shadow_mode": {"success": False, "time_ms": 0},
                        "active_mode": {"success": False, "time_ms": 0},
                        "total_time_ms": 0,
                        "improvement": 0,
                    }
                )

        return self._calculate_metrics()

    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate benchmark metrics"""
        if not self.results:
            return {"error": "No results to analyze"}

        # Calculate averages
        shadow_successes = sum(
            1 for r in self.results if r.get("shadow_mode", {}).get("success", False)
        )
        active_successes = sum(
            1 for r in self.results if r.get("active_mode", {}).get("success", False)
        )

        shadow_avg_time = sum(
            r.get("shadow_mode", {}).get("time_ms", 0) for r in self.results
        ) / len(self.results)
        active_avg_time = sum(
            r.get("active_mode", {}).get("time_ms", 0) for r in self.results
        ) / len(self.results)

        shadow_success_rate = (shadow_successes / len(self.results)) * 100
        active_success_rate = (active_successes / len(self.results)) * 100

        improvement = active_success_rate - shadow_success_rate
        time_overhead = (
            ((active_avg_time - shadow_avg_time) / shadow_avg_time) * 100
            if shadow_avg_time > 0
            else 0
        )

        return {
            "total_scenarios": len(self.results),
            "shadow_mode": {
                "success_rate": shadow_success_rate,
                "avg_time_ms": shadow_avg_time,
            },
            "active_mode": {
                "success_rate": active_success_rate,
                "avg_time_ms": active_avg_time,
            },
            "improvement": {
                "success_rate_delta": improvement,
                "time_overhead_percent": time_overhead,
            },
            "criteria": {
                "success_rate_improvement_ok": improvement >= 10,
                "time_overhead_ok": time_overhead <= 15,
                "overall_pass": improvement >= 10 and time_overhead <= 15,
            },
        }

    def print_results(self, metrics: Dict[str, Any]):
        """Print benchmark results"""
        print("\n" + "=" * 60)
        print("S2 VENDORS BENCHMARK RESULTS")
        print("=" * 60)

        print("\nShadow Mode:")
        print(f"  Success Rate: {metrics['shadow_mode']['success_rate']:.1f}%")
        print(f"  Avg Time: {metrics['shadow_mode']['avg_time_ms']:.1f}ms")

        print("\nActive Mode:")
        print(f"  Success Rate: {metrics['active_mode']['success_rate']:.1f}%")
        print(f"  Avg Time: {metrics['active_mode']['avg_time_ms']:.1f}ms")

        print("\nImprovement:")
        print(
            f"  Success Rate Delta: {metrics['improvement']['success_rate_delta']:+.1f} pts"
        )
        print(
            f"  Time Overhead: {metrics['improvement']['time_overhead_percent']:+.1f}%"
        )

        print("\nCriteria:")
        print(
            f"  Success Rate Improvement ≥ +10 pts: {'✓' if metrics['criteria']['success_rate_improvement_ok'] else '✗'}"
        )
        print(
            f"  Time Overhead ≤ +15%: {'✓' if metrics['criteria']['time_overhead_ok'] else '✗'}"
        )
        print(f"  Overall Pass: {'✓' if metrics['criteria']['overall_pass'] else '✗'}")

        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="S2 Vendors Benchmark")
    parser.add_argument(
        "--mode",
        choices=["shadow", "active", "both"],
        default="both",
        help="Benchmark mode",
    )
    parser.add_argument("--output", help="Output file for results")

    args = parser.parse_args()

    benchmark = S2VendorsBenchmark()
    metrics = benchmark.run_benchmark(args.mode)

    benchmark.print_results(metrics)

    if args.output:
        with open(args.output, "w") as f:
            json.dump({"metrics": metrics, "results": benchmark.results}, f, indent=2)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
