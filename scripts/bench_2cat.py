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
from concurrent.futures import ProcessPoolExecutor, as_completed

from proofengine.metrics import enforce_fairness_gate
from proofengine.cache.aggressive import cache_manager
from proofengine.profiler.system import (
    start_profiling,
    stop_profiling,
    get_performance_report,
)


def run_case_worker(args_tuple):
    """Worker function for parallel case execution."""
    mode, case, verifier, llm, run_id = args_tuple

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
        "case_id": case["id"],
        "run_id": run_id,
        "ok": rc.returncode == 0,
        "ms": dur_ms,
        "stdout": rc.stdout[-1000:],
        "stderr": rc.stderr[-1000:],
    }


def run_once(
    mode: str, case: Dict[str, str], verifier: str = "docker", llm: str = "disabled"
) -> Dict[str, Any]:
    """Run a single benchmark case (legacy function for compatibility)."""
    result = run_case_worker((mode, case, verifier, llm, 0))
    return {
        "ok": result["ok"],
        "ms": result["ms"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
    }


def median_ms(samples: List[Dict[str, Any]]) -> float:
    """Calculate median execution time from samples."""
    return statistics.median([s["ms"] for s in samples])


def run_sequential_benchmark(suite: Dict[str, Any], args) -> Dict[str, Any]:
    """Run benchmark sequentially (original behavior)."""
    results = {
        "mode": args.mode,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cases": [],
    }

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

    return results


def run_parallel_benchmark(suite: Dict[str, Any], args) -> Dict[str, Any]:
    """Run benchmark with parallel execution."""
    results = {
        "mode": args.mode,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cases": [],
    }

    # Prepare all tasks
    tasks = []
    for case in suite["cases"]:
        for run in range(args.runs):
            tasks.append((args.mode, case, args.verifier, args.llm, run))

    print(f"  Total tasks: {len(tasks)}")

    # Execute in parallel
    case_results = {}
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        future_to_task = {
            executor.submit(run_case_worker, task): task for task in tasks
        }

        completed = 0
        for future in as_completed(future_to_task):
            result = future.result()
            case_id = result["case_id"]

            if case_id not in case_results:
                case_results[case_id] = []
            case_results[case_id].append(result)

            completed += 1
            if completed % args.workers == 0:
                print(f"    Completed: {completed}/{len(tasks)}")

    # Aggregate results by case
    for case in suite["cases"]:
        case_id = case["id"]
        if case_id in case_results:
            samples = case_results[case_id]
            ok = all(s["ok"] for s in samples)
            median_time = median_ms(samples)

            results["cases"].append(
                {
                    "id": case_id,
                    "ok": ok,
                    "median_ms": median_time,
                    "runs": [{"ok": s["ok"], "ms": s["ms"]} for s in samples],
                }
            )

            print(f"  Case {case_id}: {'OK' if ok else 'FAIL'}, {median_time:.1f}ms")

    return results


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
    parser.add_argument(
        "--workers", type=int, default=1, help="Number of parallel workers"
    )
    parser.add_argument(
        "--parallel", action="store_true", help="Enable parallel execution"
    )
    parser.add_argument(
        "--profile", action="store_true", help="Enable performance profiling"
    )
    parser.add_argument("--cache-warmup", help="Warm up caches from file")
    parser.add_argument(
        "--compact-json", action="store_true", help="Use compact JSON format"
    )

    args = parser.parse_args()

    # Performance optimizations
    if args.profile:
        print("🔍 Starting performance profiling...")
        start_profiling()

    if args.cache_warmup:
        print(f"🔥 Warming up caches from {args.cache_warmup}...")
        cache_manager.warmup_from_file(args.cache_warmup)

    # Load benchmark suite
    suite = json.loads(Path(args.suite).read_text())

    results = {
        "mode": args.mode,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cases": [],
    }

    print(f"Running {args.mode} mode with {args.runs} runs per case...")

    if args.parallel and args.workers > 1:
        print(f"🚀 Parallel execution with {args.workers} workers")
        results = run_parallel_benchmark(suite, args)
    else:
        print("🐌 Sequential execution")
        results = run_sequential_benchmark(suite, args)

    # Save results
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    # Use compact JSON if requested
    if args.compact_json:
        json_str = json.dumps(results, separators=(",", ":"))
    else:
        json_str = json.dumps(results, indent=2)

    Path(args.out).write_text(json_str)
    print(f"Results saved to: {args.out}")

    # Performance profiling results
    if args.profile:
        stop_profiling()
        performance_report = get_performance_report()

        # Save performance report
        perf_out = args.out.replace(".json", "_performance.json")
        Path(perf_out).write_text(json.dumps(performance_report, indent=2))
        print(f"Performance report saved to: {perf_out}")

        # Print cache statistics
        cache_stats = cache_manager.get_all_stats()
        print(f"Cache stats: {cache_stats}")

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
