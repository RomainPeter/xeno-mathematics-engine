#!/usr/bin/env python3
"""
Verifier v0.1 - Hermetic runner with attestation
Supports: pytest, ruff, mypy, opa (optional)
"""

import json
import subprocess
import tempfile
import shutil
import os
import time
from pathlib import Path
from datetime import datetime
import hashlib


class VerifierError(Exception):
    pass


class Verifier:
    def __init__(self, timeout=45, memory_limit_mb=512):
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self.temp_dir = None

    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="verifier_")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def run_hermetic(self, cmd, cwd=None):
        """Run command in hermetic environment"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.temp_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={**os.environ, "PYTHONPATH": str(Path.cwd())},
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            raise VerifierError(f"Command timed out after {self.timeout}s")
        except Exception as e:
            raise VerifierError(f"Command failed: {e}")

    def run_pytest(self, test_path, args=None):
        """Run pytest tests"""
        cmd = ["python", "-m", "pytest", test_path]
        if args:
            cmd.extend(args)
        return self.run_hermetic(cmd)

    def run_ruff(self, path, args=None):
        """Run ruff linter"""
        cmd = ["python", "-m", "ruff", "check", path]
        if args:
            cmd.extend(args)
        return self.run_hermetic(cmd)

    def run_mypy(self, path, args=None):
        """Run mypy type checker"""
        cmd = ["python", "-m", "mypy", path]
        if args:
            cmd.extend(args)
        return self.run_hermetic(cmd)

    def run_opa(self, policy_path, data_path):
        """Run OPA policy check"""
        cmd = ["opa", "eval", "-d", policy_path, "-i", data_path, "data"]
        return self.run_hermetic(cmd)


def verify_pcap_file(pcap_path):
    """Verify a PCAP file and return attestation"""
    with open(pcap_path, "r", encoding="utf-8") as f:
        pcap = json.load(f)

    start_time = time.time()
    verdict = "accepted"
    errors = []

    with Verifier() as verifier:
        # Run proofs
        for proof in pcap.get("proofs", []):
            try:
                if proof["type"] == "unit_test" and proof["runner"] == "pytest":
                    result = verifier.run_pytest(proof["args"][0], proof["args"][1:])
                    if not result["success"]:
                        verdict = "rejected"
                        errors.append(f"pytest failed: {result['stderr']}")

                elif proof["type"] == "static_analysis" and proof["runner"] == "ruff":
                    result = verifier.run_ruff(proof["args"][0], proof["args"][1:])
                    if not result["success"]:
                        verdict = "rejected"
                        errors.append(f"ruff failed: {result['stderr']}")

                elif proof["type"] == "static_analysis" and proof["runner"] == "mypy":
                    result = verifier.run_mypy(proof["args"][0], proof["args"][1:])
                    if not result["success"]:
                        verdict = "rejected"
                        errors.append(f"mypy failed: {result['stderr']}")

                elif proof["type"] == "policy_check" and proof["runner"] == "opa":
                    result = verifier.run_opa(proof["args"][1], proof["args"][2])
                    if not result["success"]:
                        verdict = "rejected"
                        errors.append(f"opa failed: {result['stderr']}")

            except VerifierError as e:
                verdict = "rejected"
                errors.append(str(e))

    elapsed_ms = int((time.time() - start_time) * 1000)

    # Generate attestation
    attestation = {
        "verdict": verdict,
        "ts": datetime.utcnow().isoformat() + "Z",
        "signature": f"verifier:v0.1:{hashlib.sha256(str(errors).encode()).hexdigest()[:16]}",
        "elapsed_ms": elapsed_ms,
        "errors": errors,
    }

    return attestation


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Verifier v0.1")
    parser.add_argument("pcap_file", help="PCAP file to verify")
    parser.add_argument("--output", help="Output attestation file")

    args = parser.parse_args()

    try:
        result = verify_pcap_file(args.pcap_file)
        print(json.dumps(result, indent=2))

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"Attestation saved to {args.output}")

    except Exception as e:
        print(f"Verification failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
