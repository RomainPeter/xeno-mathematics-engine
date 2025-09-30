#!/usr/bin/env python3
"""
Budget and Timeout Calibration Script
Calibrates p95 verify_ms budgets and timeouts based on historical data
"""
import json
from pathlib import Path
from typing import Dict, List, Any


class BudgetCalibrator:
    """Calibrates budgets and timeouts for Discovery Engine 2-Cat."""

    def __init__(self):
        self.metrics_file = Path("out/metrics.json")
        self.domain_spec_file = Path("domain/regtech_code/domain_spec.json")
        self.overrides_file = Path("out/overrides.json")
        self.historical_data = []

    def load_historical_metrics(self) -> List[Dict[str, Any]]:
        """Load historical metrics from various sources."""
        metrics_sources = [
            "out/metrics.json",
            "artifacts/bench_public/metrics_baseline.json",
            "artifacts/bench_public/metrics_active.json",
            "out/bench/metrics.json",
        ]

        all_metrics = []
        for source in metrics_sources:
            if Path(source).exists():
                try:
                    with open(source) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            all_metrics.extend(data)
                        else:
                            all_metrics.append(data)
                except Exception as e:
                    print(f"⚠️ Could not load {source}: {e}")

        return all_metrics

    def extract_timing_metrics(
        self, metrics: List[Dict[str, Any]]
    ) -> Dict[str, List[float]]:
        """Extract timing metrics from historical data."""
        timing_data = {
            "verify_ms": [],
            "normalize_ms": [],
            "meet_ms": [],
            "total_ms": [],
        }

        for metric in metrics:
            # Extract verify timing
            if "verify" in metric:
                verify_data = metric["verify"]
                if isinstance(verify_data, dict) and "ms" in verify_data:
                    timing_data["verify_ms"].append(verify_data["ms"])
                elif isinstance(verify_data, list):
                    for v in verify_data:
                        if isinstance(v, dict) and "ms" in v:
                            timing_data["verify_ms"].append(v["ms"])

            # Extract normalize timing
            if "normalize" in metric:
                norm_data = metric["normalize"]
                if isinstance(norm_data, dict) and "ms" in norm_data:
                    timing_data["normalize_ms"].append(norm_data["ms"])

            # Extract meet timing
            if "meet" in metric:
                meet_data = metric["meet"]
                if isinstance(meet_data, dict) and "ms" in meet_data:
                    timing_data["meet_ms"].append(meet_data["ms"])

            # Extract total timing
            if "total_ms" in metric:
                timing_data["total_ms"].append(metric["total_ms"])
            elif "timing" in metric and "total_ms" in metric["timing"]:
                timing_data["total_ms"].append(metric["timing"]["total_ms"])

        return timing_data

    def calculate_p95_budgets(
        self, timing_data: Dict[str, List[float]]
    ) -> Dict[str, float]:
        """Calculate p95 budgets for each operation."""
        budgets = {}

        for operation, times in timing_data.items():
            if times:
                # Calculate p95 (95th percentile)
                sorted_times = sorted(times)
                p95_index = int(0.95 * len(sorted_times))
                p95_value = (
                    sorted_times[p95_index]
                    if p95_index < len(sorted_times)
                    else sorted_times[-1]
                )

                # Add 20% safety margin
                budgets[operation] = p95_value * 1.2

                print(
                    f"📊 {operation}: p95 = {p95_value:.2f}ms, budget = {budgets[operation]:.2f}ms"
                )
            else:
                # Default values if no historical data
                default_budgets = {
                    "verify_ms": 5000.0,
                    "normalize_ms": 1000.0,
                    "meet_ms": 2000.0,
                    "total_ms": 10000.0,
                }
                budgets[operation] = default_budgets.get(operation, 5000.0)
                print(
                    f"⚠️ {operation}: No historical data, using default = {budgets[operation]:.2f}ms"
                )

        return budgets

    def calculate_timeouts(self, budgets: Dict[str, float]) -> Dict[str, float]:
        """Calculate timeouts based on budgets."""
        timeouts = {}

        # Timeouts are typically 2x the p95 budget for safety
        for operation, budget in budgets.items():
            timeouts[operation] = budget * 2.0
            print(f"⏱️ {operation}: timeout = {timeouts[operation]:.2f}ms")

        return timeouts

    def generate_overrides(
        self, budgets: Dict[str, float], timeouts: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate overrides configuration."""
        overrides = {
            "version": "v0.1.1",
            "calibration_date": "2024-01-15",
            "budgets": {
                "verify_ms": {
                    "p95": budgets.get("verify_ms", 5000.0),
                    "timeout": timeouts.get("verify_ms", 10000.0),
                    "safety_margin": 0.2,
                },
                "normalize_ms": {
                    "p95": budgets.get("normalize_ms", 1000.0),
                    "timeout": timeouts.get("normalize_ms", 2000.0),
                    "safety_margin": 0.2,
                },
                "meet_ms": {
                    "p95": budgets.get("meet_ms", 2000.0),
                    "timeout": timeouts.get("meet_ms", 4000.0),
                    "safety_margin": 0.2,
                },
                "total_ms": {
                    "p95": budgets.get("total_ms", 10000.0),
                    "timeout": timeouts.get("total_ms", 20000.0),
                    "safety_margin": 0.2,
                },
            },
            "timeouts": {
                "operation_timeout": max(timeouts.values()),
                "global_timeout": max(timeouts.values()) * 1.5,
                "retry_timeout": min(timeouts.values()) * 0.5,
            },
            "calibration_stats": {
                "samples_used": len(self.historical_data),
                "confidence_level": 0.95,
                "safety_margin": 0.2,
            },
        }

        return overrides

    def update_domain_spec(self, overrides: Dict[str, Any]) -> bool:
        """Update domain spec with calibrated budgets."""
        if not self.domain_spec_file.exists():
            print(f"⚠️ Domain spec file not found: {self.domain_spec_file}")
            return False

        try:
            with open(self.domain_spec_file) as f:
                domain_spec = json.load(f)

            # Update budgets in domain spec
            if "budgets" not in domain_spec:
                domain_spec["budgets"] = {}

            for operation, budget_config in overrides["budgets"].items():
                domain_spec["budgets"][operation] = {
                    "p95": budget_config["p95"],
                    "timeout": budget_config["timeout"],
                }

            # Update timeouts
            if "timeouts" not in domain_spec:
                domain_spec["timeouts"] = {}

            domain_spec["timeouts"].update(overrides["timeouts"])

            # Add calibration metadata
            domain_spec["calibration"] = {
                "version": overrides["version"],
                "date": overrides["calibration_date"],
                "stats": overrides["calibration_stats"],
            }

            # Write updated domain spec
            with open(self.domain_spec_file, "w") as f:
                json.dump(domain_spec, f, indent=2)

            print(f"✅ Updated domain spec: {self.domain_spec_file}")
            return True

        except Exception as e:
            print(f"❌ Failed to update domain spec: {e}")
            return False

    def save_overrides(self, overrides: Dict[str, Any]) -> bool:
        """Save overrides to file."""
        try:
            with open(self.overrides_file, "w") as f:
                json.dump(overrides, f, indent=2)

            print(f"✅ Saved overrides: {self.overrides_file}")
            return True

        except Exception as e:
            print(f"❌ Failed to save overrides: {e}")
            return False

    def run_calibration(self) -> bool:
        """Run the full calibration process."""
        print("🔧 Starting budget and timeout calibration...")

        # Load historical data
        print("📊 Loading historical metrics...")
        self.historical_data = self.load_historical_metrics()
        print(f"   Loaded {len(self.historical_data)} historical records")

        if not self.historical_data:
            print("⚠️ No historical data found, using defaults")

        # Extract timing metrics
        print("⏱️ Extracting timing metrics...")
        timing_data = self.extract_timing_metrics(self.historical_data)

        # Calculate p95 budgets
        print("📈 Calculating p95 budgets...")
        budgets = self.calculate_p95_budgets(timing_data)

        # Calculate timeouts
        print("⏰ Calculating timeouts...")
        timeouts = self.calculate_timeouts(budgets)

        # Generate overrides
        print("📋 Generating overrides...")
        overrides = self.generate_overrides(budgets, timeouts)

        # Save overrides
        if not self.save_overrides(overrides):
            return False

        # Update domain spec
        if not self.update_domain_spec(overrides):
            return False

        print("✅ Budget and timeout calibration completed!")
        print(f"📊 Calibrated {len(budgets)} operations")
        print(f"⏱️ Set {len(timeouts)} timeouts")
        print(f"📁 Overrides saved to: {self.overrides_file}")

        return True


def main():
    """Main calibration function."""
    calibrator = BudgetCalibrator()
    success = calibrator.run_calibration()

    if success:
        print("🎉 Budget calibration completed successfully!")
        exit(0)
    else:
        print("❌ Budget calibration failed!")
        exit(1)


if __name__ == "__main__":
    main()
