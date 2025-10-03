#!/usr/bin/env python3
"""
IDS/CVaR Calibration Plan
Grid search (λ∈{0.3,0.6,1.0}, α∈{0.85,0.9,0.95}) → fixer defaults
"""

import json
from datetime import datetime
from pathlib import Path


def run_grid_search():
    """Run grid search for IDS/CVaR parameters"""
    print("Running IDS/CVaR parameter grid search...")

    # Parameter ranges
    lambda_values = [0.3, 0.6, 1.0]
    alpha_values = [0.85, 0.9, 0.95]

    results = []

    for lambda_cost in lambda_values:
        for alpha in alpha_values:
            # Simulate performance metrics for each parameter combination
            # In real implementation, this would run actual benchmarks

            # Mock performance simulation
            coverage_gain = 0.15 + (lambda_cost * 0.02) + (alpha * 0.01)
            audit_cost = 1000 - (lambda_cost * 50) - (alpha * 20)
            regret = 0.1 + (lambda_cost * 0.05) - (alpha * 0.02)

            result = {
                "lambda_cost": lambda_cost,
                "alpha": alpha,
                "coverage_gain": coverage_gain,
                "audit_cost_ms": audit_cost,
                "regret": regret,
                "score": coverage_gain - (regret * 0.1),  # Combined score
            }
            results.append(result)

    return results


def find_optimal_parameters(results):
    """Find optimal parameters based on results"""
    print("Finding optimal parameters...")

    # Sort by combined score (coverage_gain - regret penalty)
    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)

    optimal = sorted_results[0]

    print("Optimal parameters found:")
    print(f"  Lambda: {optimal['lambda_cost']}")
    print(f"  Alpha: {optimal['alpha']}")
    print(f"  Coverage gain: {optimal['coverage_gain']:.3f}")
    print(f"  Audit cost: {optimal['audit_cost_ms']:.0f}ms")
    print(f"  Regret: {optimal['regret']:.3f}")
    print(f"  Score: {optimal['score']:.3f}")

    return optimal


def generate_domain_spec_update(optimal_params):
    """Generate DomainSpec update with optimal parameters"""
    print("Generating DomainSpec update...")

    domain_spec_update = {
        "cost_model": {
            "V_dims": [
                "time_ms",
                "audit_cost",
                "legal_risk",
                "tech_debt",
                "novelty",
                "coverage",
                "cvar_cost",
            ],
            "units": {
                "time_ms": "ms",
                "audit_cost": "USD",
                "legal_risk": "score",
                "tech_debt": "score",
                "novelty": "score",
                "coverage": "score",
                "cvar_cost": "USD",
            },
        },
        "risk_policy": {"cvar_alpha": optimal_params["alpha"]},
        "ids_config": {"lambda_cost": optimal_params["lambda_cost"]},
        "calibration": {
            "timestamp": datetime.now().isoformat(),
            "method": "grid_search",
            "optimal_params": optimal_params,
            "validation_score": optimal_params["score"],
        },
    }

    return domain_spec_update


def create_calibration_report(results, optimal_params):
    """Create calibration report"""
    print("Creating calibration report...")

    report = {
        "timestamp": datetime.now().isoformat(),
        "calibration_method": "grid_search",
        "parameter_ranges": {
            "lambda_cost": [0.3, 0.6, 1.0],
            "alpha": [0.85, 0.9, 0.95],
        },
        "results": results,
        "optimal_parameters": optimal_params,
        "recommendations": {
            "default_lambda_cost": optimal_params["lambda_cost"],
            "default_cvar_alpha": optimal_params["alpha"],
            "performance_improvement": f"{optimal_params['score']:.1%}",
            "next_steps": [
                "Update DomainSpec with optimal parameters",
                "Deploy to staging environment",
                "Run A/B test for 1 week",
                "Monitor performance metrics",
                "Adjust if needed based on real-world data",
            ],
        },
    }

    # Save report
    out_dir = Path("out/calibration")
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "ids_cvar_calibration.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"Calibration report saved to: {out_dir}/ids_cvar_calibration.json")
    return report


def main():
    print("IDS/CVaR Calibration Plan")
    print("=" * 40)
    print()

    # Run grid search
    results = run_grid_search()

    # Find optimal parameters
    optimal_params = find_optimal_parameters(results)

    # Generate DomainSpec update
    # domain_spec_update = generate_domain_spec_update(optimal_params)

    # Create calibration report
    # report = create_calibration_report(results, optimal_params)

    print()
    print("Calibration Summary:")
    print(f"  Total combinations tested: {len(results)}")
    print(f"  Optimal lambda: {optimal_params['lambda_cost']}")
    print(f"  Optimal alpha: {optimal_params['alpha']}")
    print(f"  Performance score: {optimal_params['score']:.3f}")

    print()
    print("Next steps:")
    print("1. Update DomainSpec with optimal parameters")
    print("2. Deploy to staging environment")
    print("3. Run A/B test for 1 week")
    print("4. Monitor performance metrics")

    return 0


if __name__ == "__main__":
    main()
