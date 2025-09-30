#!/usr/bin/env python3
"""
Pack signing utilities with cosign and other providers.
"""
from __future__ import annotations
from pathlib import Path
import os
import subprocess
from typing import Optional


def sign_with_cosign(
    artifact: Path,
    key_ref: Optional[str] = None,
    *,
    cosign_path: Optional[str] = None,
    dry_run: bool = False,
) -> Path:
    """
    Sign an artifact using cosign.

    Args:
        artifact: Path to the artifact to sign
        key_ref: Optional key reference for signing

    Returns:
        Path to the signature file

    Raises:
        Exception: If signing fails
    """
    artifact_path = Path(artifact)
    sig_path = artifact_path.with_suffix(artifact_path.suffix + ".sig")

    # Build cosign command
    cosign_bin = cosign_path or os.environ.get("PEFC_COSIGN_PATH") or "cosign"
    cmd = [cosign_bin, "sign-blob"]

    if key_ref:
        cmd.extend(["--key", key_ref])

    cmd.append(str(artifact_path))

    # Execute cosign command
    if dry_run:
        # Simulate a signature deterministically based on file content hash
        import hashlib

        h = hashlib.sha256()
        with open(artifact_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        sig_path.write_text(h.hexdigest())
        return sig_path

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    # Write signature to file
    if result.stdout.strip():
        sig_path.write_text(result.stdout.strip())

    return sig_path


def sign_with_sha256(artifact: Path) -> Path:
    """
    Create a SHA256 signature for an artifact.

    Args:
        artifact: Path to the artifact to sign

    Returns:
        Path to the signature file
    """
    import hashlib

    artifact_path = Path(artifact)
    sig_path = artifact_path.with_suffix(artifact_path.suffix + ".sha256")

    # Compute SHA256
    sha256_hash = hashlib.sha256()
    with open(artifact_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    # Write signature file
    sig_content = f"{sha256_hash.hexdigest()}  {artifact_path.name}\n"
    sig_path.write_text(sig_content)

    return sig_path
