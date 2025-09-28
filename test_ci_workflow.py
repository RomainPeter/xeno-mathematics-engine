#!/usr/bin/env python3
"""
Test CI workflow locally.
"""
import subprocess
import sys
import tempfile
from pathlib import Path


def test_ci_workflow():
    """Test the CI workflow steps locally."""
    print("Testing CI workflow locally...")

    with tempfile.TemporaryDirectory():

        # Step 1: Build pack
        print("\nStep 1: Building pack...")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pefc.cli",
                    "--config",
                    "config/pack.yaml",
                    "--json-logs",
                    "pack",
                    "build",
                    "--pipeline",
                    "config/pipelines/bench_pack.yaml",
                    "--no-strict",
                ],
                capture_output=True,
                text=True,
                cwd=".",
            )

            if result.returncode != 0:
                print(f"ERROR: Build failed: {result.stderr}")
                return False

            print("SUCCESS: Pack built successfully")
            print(f"INFO: Build output: {result.stdout[:200]}...")

        except Exception as e:
            print(f"ERROR: Build error: {e}")
            return False

        # Step 2: Locate zip
        print("\nStep 2: Locating zip...")
        dist_path = Path("dist")
        if not dist_path.exists():
            print("ERROR: No dist directory found")
            return False

        # Look for the newest zip file
        zip_files = []
        for pattern in ["dist/*.zip", "dist/dist/*.zip"]:
            zip_files.extend(Path(".").glob(pattern))

        if not zip_files:
            print("ERROR: No zip files found in dist/")
            return False

        # Get the newest zip file
        zip_path = max(zip_files, key=lambda p: p.stat().st_mtime)
        print(f"SUCCESS: Found zip: {zip_path}")

        # Step 3: Check for duplicates
        print("\nStep 3: Checking for duplicate arcnames...")
        try:
            result = subprocess.run(
                [sys.executable, "scripts/check_zip_duplicates.py", str(zip_path)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"ERROR: Duplicate check failed: {result.stderr}")
                return False

            print("SUCCESS: No duplicates found")
            print(f"INFO: Check output: {result.stdout}")

        except Exception as e:
            print(f"ERROR: Duplicate check error: {e}")
            return False

        # Step 4: Verify manifest/merkle
        print("\nStep 4: Verifying manifest/merkle...")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pefc.cli",
                    "pack",
                    "verify",
                    "--zip",
                    str(zip_path),
                    "--strict",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"ERROR: Verify failed: {result.stderr}")
                return False

            print("SUCCESS: Verification passed")
            print(f"INFO: Verify output: {result.stdout[:200]}...")

        except Exception as e:
            print(f"ERROR: Verify error: {e}")
            return False

        # Step 5: Extract manifest
        print("\nStep 5: Extracting manifest...")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pefc.cli",
                    "pack",
                    "manifest",
                    "--zip",
                    str(zip_path),
                    "--print",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"ERROR: Manifest extraction failed: {result.stderr}")
                return False

            print("SUCCESS: Manifest extracted")
            print(f"INFO: Manifest: {result.stdout[:200]}...")

        except Exception as e:
            print(f"ERROR: Manifest extraction error: {e}")
            return False

        print("\nSUCCESS: All CI workflow steps passed!")
        return True


if __name__ == "__main__":
    success = test_ci_workflow()
    sys.exit(0 if success else 1)
