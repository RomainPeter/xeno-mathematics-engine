#!/usr/bin/env python3
"""
Determinism E2E Test
3 runs with same seeds → identical Merkle root; variance V_actual ≤ 2%
"""

import json
import os
import subprocess
from pathlib import Path


def run_discovery_engine(seed=42):
    """Run discovery engine with specific seed"""
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(seed)
    env["DISCOVERY_SEED"] = str(seed)

    # Run the discovery engine
    result = subprocess.run(
        ["python", "scripts/demo_regtech_bench.py"],
        env=env,
        capture_output=True,
        text=True,
        cwd=".",
    )

    return result.returncode, result.stdout, result.stderr


def get_merkle_root():
    """Get current Merkle root"""
    merkle_path = Path("out/journal/merkle.txt")
    if merkle_path.exists():
        return merkle_path.read_text().strip()
    return None


def get_metrics():
    """Get current metrics"""
    metrics_path = Path("out/metrics.json")
    if metrics_path.exists():
        with open(metrics_path) as f:
            return json.load(f)
    return None


def test_determinism():
    """Test determinism across 3 runs"""
    print("🧪 Testing determinism across 3 runs...")

    # Clean previous runs
    if Path("out").exists():
        import shutil

        shutil.rmtree("out")

    merkle_roots = []
    metrics_list = []

    for run in range(3):
        print(f"  Run {run + 1}/3...")

        # Run discovery engine
        returncode, stdout, stderr = run_discovery_engine(seed=42)

        if returncode != 0:
            print(f"    ❌ Run {run + 1} failed: {stderr}")
            return False

        # Get Merkle root
        merkle_root = get_merkle_root()
        if merkle_root:
            merkle_roots.append(merkle_root)
            print(f"    📊 Merkle root: {merkle_root[:16]}...")

        # Get metrics
        metrics = get_metrics()
        if metrics:
            metrics_list.append(metrics)
            coverage = metrics.get("coverage", {}).get("coverage_gain", 0)
            novelty = metrics.get("novelty", {}).get("avg", 0)
            print(f"    📈 Coverage: {coverage:.3f}, Novelty: {novelty:.3f}")

        # Clean for next run
        if Path("out").exists():
            import shutil

            shutil.rmtree("out")

    # Check Merkle roots are identical
    if len(set(merkle_roots)) != 1:
        print(f"❌ Merkle roots differ: {merkle_roots}")
        return False

    # Check metrics variance
    if len(metrics_list) >= 2:
        coverage_values = [m.get("coverage", {}).get("coverage_gain", 0) for m in metrics_list]
        novelty_values = [m.get("novelty", {}).get("avg", 0) for m in metrics_list]

        coverage_variance = max(coverage_values) - min(coverage_values)
        novelty_variance = max(novelty_values) - min(novelty_values)

        if coverage_variance > 0.02:  # 2% threshold
            print(f"❌ Coverage variance too high: {coverage_variance:.3f} > 0.02")
            return False

        if novelty_variance > 0.02:  # 2% threshold
            print(f"❌ Novelty variance too high: {novelty_variance:.3f} > 0.02")
            return False

        print(f"✅ Coverage variance: {coverage_variance:.3f} ≤ 0.02")
        print(f"✅ Novelty variance: {novelty_variance:.3f} ≤ 0.02")

    print("✅ Determinism test passed!")
    print(f"✅ Merkle root consistent: {merkle_roots[0][:16]}...")

    return True


if __name__ == "__main__":
    success = test_determinism()
    exit(0 if success else 1)
