"""
Demo script for RegTech mini-benchmark.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def run_demo():
    """Run the RegTech demo."""
    print("🚀 Starting RegTech Discovery Engine Demo")
    print("=" * 50)

    # Mock demo results
    results = {
        "implications_accepted": 4,
        "counterexamples_found": 2,
        "rules_generated": 2,
        "journal_entries": 6,
    }

    # Create output directory
    artifacts_dir = project_root / "out"
    artifacts_dir.mkdir(exist_ok=True)

    # Export mock results
    metrics_file = artifacts_dir / "metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Demo completed with {results['implications_accepted']} implications")
    print(f"📁 Artifacts in: {artifacts_dir}")

    return results


if __name__ == "__main__":
    run_demo()
