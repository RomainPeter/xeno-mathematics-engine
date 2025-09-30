#!/usr/bin/env python3
"""
Simple demo script for CI
"""
import os
import json
import time


def main():
    """Simple demo that creates basic artifacts"""
    print("🚀 Running simple demo...")

    # Create output directory
    os.makedirs("out", exist_ok=True)
    os.makedirs("out/metrics", exist_ok=True)

    # Create simple summary
    summary = {
        "timestamp": time.time(),
        "demo_type": "simple",
        "status": "completed",
        "artifacts_created": ["out/metrics/summary.json", "out/demo_log.json"],
    }

    # Write summary
    with open("out/metrics/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Write demo log
    demo_log = {
        "steps": [
            {"step": 1, "action": "create_directories", "status": "success"},
            {"step": 2, "action": "write_summary", "status": "success"},
            {"step": 3, "action": "write_log", "status": "success"},
        ],
        "total_steps": 3,
        "success_rate": 1.0,
    }

    with open("out/demo_log.json", "w") as f:
        json.dump(demo_log, f, indent=2)

    print("✅ Demo completed successfully")
    print(f"📊 Summary: {summary}")


if __name__ == "__main__":
    main()
