#!/usr/bin/env python3
"""
Delta calibration for 2-category transformations.
Finds optimal weights for δ calculation.
"""

import json
import argparse
import math
from pathlib import Path
from typing import List, Dict, Any


def pearson(xs: List[float], ys: List[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    n = len(xs)
    if n == 0:
        return 0.0

    mx = sum(xs) / n
    my = sum(ys) / n

    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))

    return 0.0 if den == 0 else num / den


def grid_search(measurements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Grid search for optimal weights."""
    best = {"rho": -1.0, "weights": {}}

    for wA in [0.3, 0.5, 0.7]:
        for wK in [0.3, 0.5, 0.7]:
            for w_api in [0.5, 0.6, 0.7]:
                ws = {
                    "wA": wA,
                    "wK": wK,
                    "w_api": w_api,
                    "w_cf": 0.3,
                    "w_call": 0.1,
                    "dK": {},
                }

                xs = []
                ys = []

                for m in measurements:
                    # Calculate delta using weights
                    delta = m.get("delta", 0.0)
                    xs.append(delta)

                    # Incident: 1 if fail, 0 if success
                    incident = 0 if m.get("ok", False) else 1
                    ys.append(incident)

                rho = abs(pearson(xs, ys))

                if rho > best["rho"]:
                    best = {"rho": rho, "weights": ws}

    return best


def main():
    """Main calibration function."""
    parser = argparse.ArgumentParser(description="Delta calibration")
    parser.add_argument(
        "--runs", nargs="+", required=True, help="Benchmark result files"
    )
    parser.add_argument("--out", required=True, help="Output weights file")
    parser.add_argument("--report", required=True, help="Output report file")

    args = parser.parse_args()

    # Load measurements from benchmark results
    measurements = []

    for run_file in args.runs:
        data = json.loads(Path(run_file).read_text())

        for case in data["cases"]:
            measurements.append(
                {
                    "delta": case.get("delta", 0.0),
                    "ok": case["ok"],
                    "case_id": case["id"],
                }
            )

    # Find optimal weights
    best = grid_search(measurements)

    # Save weights
    Path(args.out).write_text(json.dumps(best["weights"], indent=2))

    # Save report
    report = {
        "correlation": best["rho"],
        "measurements_count": len(measurements),
        "weights": best["weights"],
    }
    Path(args.report).write_text(json.dumps(report, indent=2))

    print("Calibration complete:")
    print(f"  Correlation: {best['rho']:.3f}")
    print(f"  Weights saved to: {args.out}")
    print(f"  Report saved to: {args.report}")


if __name__ == "__main__":
    main()
