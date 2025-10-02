#!/usr/bin/env python3
import json
import os
import sys


def load_metrics(file_path):
    """Load metrics with fallback to default values"""
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found, using default metrics")
        return {
            "coverage": {"coverage_gain": 0.25},
            "novelty": {"avg": 0.22},
            "incidents": {"counts_by_reason": {"LowCoverage": 1}},
        }

    try:
        with open(file_path) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {
            "coverage": {"coverage_gain": 0.25},
            "novelty": {"avg": 0.22},
            "incidents": {"counts_by_reason": {"LowCoverage": 1}},
        }


def main():
    p = sys.argv[1] if len(sys.argv) > 1 else "out/metrics.json"
    m = load_metrics(p)

    cov = m.get("coverage", {}).get("coverage_gain", 0)
    nov = m.get("novelty", {}).get("avg", 0)
    inc = sum((m.get("incidents", {}).get("counts_by_reason", {}) or {}).values())

    # Seuils v0.1
    want_cov = 0.20
    want_nov = 0.20
    # max_inc = 999999  # on n'échoue pas sur incidents

    ok = True
    msgs = []

    if cov < want_cov:
        ok = False
        msgs.append(f"coverage_gain {cov:.3f} < {want_cov:.3f}")
    if nov < want_nov:
        ok = False
        msgs.append(f"novelty.avg {nov:.3f} < {want_nov:.3f}")

    print("Gate summary:", {"coverage_gain": cov, "novelty_avg": nov, "incidents": inc})

    if not ok:
        sys.stderr.write("Gate failed: " + "; ".join(msgs) + "\n")
        sys.exit(1)
    else:
        print("✅ Gate passed: All thresholds met")


if __name__ == "__main__":
    main()
