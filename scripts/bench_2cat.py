#!/usr/bin/env python3
"""
Benchmark pipeline for 2-category transformations.
Supports baseline, shadow, and active modes with real timing.
"""

import json
import argparse
import subprocess
import statistics
import time
import sys
from pathlib import Path
from typing import Dict, List, Any

from proofengine.metrics import enforce_fairness_gate


def run_once(
    mode: str, case: Dict[str, str], verifier: str = "docker", llm: str = "disabled"
) -> Dict[str, Any]:
    """Run a single benchmark case."""
    cmd = [
        "python",
        "orchestrator/run.py",
        "--mode",
        mode,
        "--plan",
        case["plan"],
        "--state",
        case["state"],
        "--verifier",
        verifier,
    ]

    if llm == "disabled":
        cmd += ["--disable-llm"]

    t0 = time.perf_counter()
    rc = subprocess.run(cmd, capture_output=True, text=True)
    dur_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "ok": rc.returncode == 0,
        "ms": dur_ms,
        "stdout": rc.stdout[-1000:],
        "stderr": rc.stderr[-1000:],
    }


def median_ms(samples: List[Dict[str, Any]]) -> float:
    """Calculate median execution time from samples."""
    return statistics.median([s["ms"] for s in samples])


def main():
    """Main benchmark function."""
    parser = argparse.ArgumentParser(description="2-category benchmark pipeline")
    parser.add_argument("--suite", required=True, help="Benchmark suite JSON file")
    parser.add_argument(
        "--mode",
        choices=["baseline", "shadow", "active"],
        required=True,
        help="Execution mode",
    )
    parser.add_argument("--runs", type=int, default=3, help="Number of runs per case")
    parser.add_argument("--out", required=True, help="Output JSON file")
    parser.add_argument("--verifier", default="docker", help="Verifier to use")
    parser.add_argument("--llm", default="disabled", help="LLM mode")
    parser.add_argument("--compare", help="Compare with baseline metrics file")
    parser.add_argument("--fairness", action="store_true", help="Enable fairness mode")

    args = parser.parse_args()

    # Load benchmark suite
    suite = json.loads(Path(args.suite).read_text())

    results = {
        "mode": args.mode,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cases": [],
    }

    print(f"Running {args.mode} mode with {args.runs} runs per case...")

    for case in suite["cases"]:
        print(f"  Case: {case['id']}")
        samples = []

        for run in range(args.runs):
            print(f"    Run {run + 1}/{args.runs}")
            sample = run_once(args.mode, case, verifier=args.verifier, llm=args.llm)
            samples.append(sample)

        ok = all(s["ok"] for s in samples)
        median_time = median_ms(samples)

        results["cases"].append(
            {
                "id": case["id"],
                "ok": ok,
                "median_ms": median_time,
                "runs": [{"ok": s["ok"], "ms": s["ms"]} for s in samples],
            }
        )

        print(f"    Result: {'OK' if ok else 'FAIL'}, {median_time:.1f}ms")

    # Save results
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(results, indent=2))
    print(f"Results saved to: {args.out}")

    # Fairness gate: compare with baseline if provided
    if args.compare and args.mode != "baseline":
        print(f"🔍 Checking fairness gate against: {args.compare}")
        try:
            enforce_fairness_gate(args.compare, args.out)
            print("✅ Fairness gate passed: WorkUnits identical")
        except SystemExit:
            print("❌ Fairness gate failed: WorkUnits differ")
            sys.exit(1)


if __name__ == "__main__":
    main()
