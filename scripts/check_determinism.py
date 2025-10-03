#!/usr/bin/env python3
"""
Determinism Check Script
Runs determinism test and reports results
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run determinism check"""
    print("🔍 Checking determinism...")

    # Ensure test directory exists
    Path("tests/e2e").mkdir(parents=True, exist_ok=True)

    # Run determinism test
    result = subprocess.run(
        [sys.executable, "tests/e2e/test_determinism.py"],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode == 0:
        print("✅ Determinism check passed!")
        return True
    else:
        print("❌ Determinism check failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
