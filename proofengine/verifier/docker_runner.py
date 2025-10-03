#!/usr/bin/env python3
"""
Docker runner for hermetic verification
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class DockerRunner:
    """Hermetic Docker runner for verification"""

    def __init__(self, image_tag: str = "proofengine/verifier:0.1.0"):
        self.image_tag = image_tag
        self.workspace_dir = Path.cwd()

    def build_image(self, force: bool = False) -> bool:
        """Build Docker image if not present or force=True"""
        try:
            # Check if image exists
            if not force:
                result = subprocess.run(
                    ["docker", "image", "inspect", self.image_tag],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    print(f"✅ Image {self.image_tag} already exists")
                    return True

            print(f"🔨 Building Docker image {self.image_tag}...")
            result = subprocess.run(
                [
                    "docker",
                    "build",
                    "-t",
                    self.image_tag,
                    "-f",
                    "Dockerfile.verifier",
                    ".",
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )

            if result.returncode == 0:
                print(f"✅ Image {self.image_tag} built successfully")
                return True
            else:
                print(f"❌ Failed to build image: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Docker build timeout")
            return False
        except Exception as e:
            print(f"❌ Docker build error: {e}")
            return False

    def run_verification(
        self,
        pcap_files: List[Path],
        timeout_s: int = 300,
        out_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Run verification in hermetic Docker container"""
        if not pcap_files:
            return {"error": "No PCAP files provided"}

        # Create output directory
        if out_dir is None:
            out_dir = Path("artifacts/verifier_out")
        out_dir.mkdir(parents=True, exist_ok=True)

        # Prepare PCAP files for container
        pcap_inputs = []
        for pcap_file in pcap_files:
            if pcap_file.exists():
                pcap_inputs.append(str(pcap_file))
            else:
                print(f"⚠️ PCAP file not found: {pcap_file}")

        if not pcap_inputs:
            return {"error": "No valid PCAP files found"}

        # Build Docker command
        cmd = [
            "docker",
            "run",
            "--rm",
            "--network=none",  # No network access
            "--cpus=1",  # CPU limit
            "-m",
            "512m",  # Memory limit
            "--pids-limit=256",  # Process limit
            "--read-only",  # Read-only filesystem
            "-v",
            f"{self.workspace_dir}:/workspace:ro",  # Mount workspace read-only
            "-v",
            f"{out_dir.absolute()}:/out:rw",  # Mount output directory
            "--tmpfs",
            "/tmp",  # Temporary filesystem
            "--tmpfs",
            "/run",  # Runtime filesystem
            "-w",
            "/workspace",  # Working directory
            self.image_tag,
            "python",
            "scripts/verifier.py",
            "--runner",
            "local",
            "--out",
            "/out",
        ]

        # Add PCAP files
        for pcap_file in pcap_inputs:
            cmd.extend(["--pcap", pcap_file])

        print("🐳 Running hermetic verification...")
        print(f"   Command: {' '.join(cmd[:10])}...")
        print(f"   PCAP files: {len(pcap_inputs)}")
        print(f"   Output: {out_dir}")

        start_time = time.time()

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)

            duration = time.time() - start_time

            # Parse results
            attestation_file = out_dir / "attestation.json"
            audit_pack_file = out_dir / "audit_pack.zip"

            result_data = {
                "exit_code": result.returncode,
                "duration_s": round(duration, 2),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "pcap_count": len(pcap_inputs),
                "attestation_exists": attestation_file.exists(),
                "audit_pack_exists": audit_pack_file.exists(),
                "output_dir": str(out_dir),
            }

            # Load attestation if available
            if attestation_file.exists():
                try:
                    with open(attestation_file, "r") as f:
                        result_data["attestation"] = json.load(f)
                except Exception as e:
                    result_data["attestation_error"] = str(e)

            if result.returncode == 0:
                print(f"✅ Verification completed in {duration:.1f}s")
            else:
                print(f"❌ Verification failed (exit code: {result.returncode})")
                print(f"   Error: {result.stderr}")

            return result_data

        except subprocess.TimeoutExpired:
            print(f"❌ Verification timeout after {timeout_s}s")
            return {
                "error": "timeout",
                "timeout_s": timeout_s,
                "duration_s": time.time() - start_time,
            }
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return {"error": str(e), "duration_s": time.time() - start_time}

    def test_egress(self) -> bool:
        """Test that egress is properly blocked"""
        print("🔒 Testing network egress blocking...")

        try:
            # Try to make network request (should fail)
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network=none",
                    "busybox:latest",
                    "sh",
                    "-c",
                    "wget -qO- https://example.com",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                print("✅ Egress properly blocked")
                return True
            else:
                print("❌ Egress unexpectedly allowed")
                return False

        except subprocess.TimeoutExpired:
            print("✅ Egress timeout (expected)")
            return True
        except Exception as e:
            print(f"❌ Egress test error: {e}")
            return False

    def get_image_info(self) -> Dict[str, Any]:
        """Get Docker image information"""
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", self.image_tag],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                info = json.loads(result.stdout)[0]
                return {
                    "tag": self.image_tag,
                    "id": info["Id"],
                    "created": info["Created"],
                    "size": info["Size"],
                    "architecture": info["Architecture"],
                    "os": info["Os"],
                }
            else:
                return {"error": "Image not found"}

        except Exception as e:
            return {"error": str(e)}
