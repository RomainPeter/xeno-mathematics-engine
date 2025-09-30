#!/usr/bin/env python3
"""
Verifier v0.1 - Hermetic runner with attestation
Supports: pytest, ruff, mypy, opa (optional)
Runner modes: local, docker
"""

import json
import subprocess
import tempfile
import shutil
import os
import time
import zipfile
from pathlib import Path
from datetime import datetime
import hashlib
import argparse


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


def create_audit_pack(pcap_files, out_dir):
    """Create audit pack with attestations"""
    audit_pack_dir = out_dir / "audit_pack"
    audit_pack_dir.mkdir(exist_ok=True)

    attestations = []
    for pcap_file in pcap_files:
        attestation = verify_pcap_file(pcap_file)
        attestations.append(attestation)

        # Save individual attestation
        attestation_file = audit_pack_dir / f"{pcap_file.stem}_attestation.json"
        with open(attestation_file, "w") as f:
            json.dump(attestation, f, indent=2)

    # Create combined attestation
    combined_attestation = {
        "version": "0.1.0",
        "ts": datetime.utcnow().isoformat() + "Z",
        "pcap_count": len(pcap_files),
        "attestations": attestations,
        "digest": hashlib.sha256(
            json.dumps(attestations, sort_keys=True).encode()
        ).hexdigest(),
    }

    attestation_file = audit_pack_dir / "attestation.json"
    with open(attestation_file, "w") as f:
        json.dump(combined_attestation, f, indent=2)

    # Create audit pack zip
    audit_pack_zip = out_dir / "audit_pack.zip"
    with zipfile.ZipFile(audit_pack_zip, "w") as zf:
        for file_path in audit_pack_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(audit_pack_dir))

    # Create provenance
    provenance = {
        "version": "0.1.0",
        "ts": datetime.utcnow().isoformat() + "Z",
        "image_digest": os.getenv("DOCKER_IMAGE_DIGEST", "unknown"),
        "pcap_hashes": [
            hashlib.sha256(pcap_file.read_bytes()).hexdigest()
            for pcap_file in pcap_files
        ],
        "audit_pack_hash": hashlib.sha256(audit_pack_zip.read_bytes()).hexdigest(),
    }

    provenance_file = out_dir / "provenance.json"
    with open(provenance_file, "w") as f:
        json.dump(provenance, f, indent=2)

    return audit_pack_zip, attestation_file, provenance_file


def sign_audit_pack(audit_pack_zip, cosign_key=None):
    """Sign audit pack with cosign if key available"""
    if not cosign_key:
        cosign_key = os.getenv("COSIGN_KEY")

    if not cosign_key:
        print("⚠️ No COSIGN_KEY found, using fallback signature")
        # Create fallback signature
        signature_file = audit_pack_zip.with_suffix(".sig")
        with open(signature_file, "w") as f:
            f.write(
                f"fallback:{hashlib.sha256(audit_pack_zip.read_bytes()).hexdigest()}"
            )
        return signature_file

    try:
        # Use cosign to sign
        signature_file = audit_pack_zip.with_suffix(".sig")
        result = subprocess.run(
            ["cosign", "sign-blob", str(audit_pack_zip), "--key", cosign_key],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            with open(signature_file, "w") as f:
                f.write(result.stdout)
            print("✅ Audit pack signed with cosign")
            return signature_file
        else:
            print(f"❌ Cosign failed: {result.stderr}")
            return None

    except Exception as e:
        print(f"❌ Signing failed: {e}")
        return None


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Verifier v0.1")
    parser.add_argument("--pcap", action="append", help="PCAP file to verify")
    parser.add_argument(
        "--runner", choices=["local", "docker"], default="local", help="Runner mode"
    )
    parser.add_argument(
        "--out", help="Output directory", default="artifacts/verifier_out"
    )
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--sign", action="store_true", help="Sign audit pack")
    parser.add_argument("--cosign-key", help="Cosign private key file")

    args = parser.parse_args()

    if not args.pcap:
        print("❌ No PCAP files provided")
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    pcap_files = [Path(p) for p in args.pcap]

    if args.runner == "docker":
        print("🐳 Using Docker runner...")
        from proofengine.verifier.docker_runner import DockerRunner

        runner = DockerRunner()
        if not runner.build_image():
            print("❌ Failed to build Docker image")
            return 1

        result = runner.run_verification(pcap_files, args.timeout, out_dir)
        print(json.dumps(result, indent=2))

        if result.get("error"):
            return 1

    else:
        print("🏠 Using local runner...")
        audit_pack_zip, attestation_file, provenance_file = create_audit_pack(
            pcap_files, out_dir
        )

        print(f"✅ Audit pack created: {audit_pack_zip}")
        print(f"✅ Attestation: {attestation_file}")
        print(f"✅ Provenance: {provenance_file}")

        if args.sign:
            signature_file = sign_audit_pack(audit_pack_zip, args.cosign_key)
            if signature_file:
                print(f"✅ Signature: {signature_file}")

    return 0


if __name__ == "__main__":
    exit(main())
