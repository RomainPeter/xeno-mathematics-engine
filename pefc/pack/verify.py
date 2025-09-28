#!/usr/bin/env python3
"""
Pack verification utilities for manifest, merkle, and signature validation.
"""
from __future__ import annotations
from zipfile import ZipFile
from pathlib import Path
import json
import hashlib
import subprocess
import shlex


def _sha256_stream(fobj, chunk=1 << 20):
    """Compute SHA256 of a file-like object in streaming fashion."""
    h = hashlib.sha256()
    while True:
        b = fobj.read(chunk)
        if not b:
            break
        h.update(b)
    return h.hexdigest()


def _compute_root_from_manifest(manifest: dict) -> str:
    """Compute Merkle root from manifest files."""
    g = hashlib.sha256()
    for e in sorted(manifest["files"], key=lambda x: x["path"]):
        g.update((e["path"] + "\n").encode())
        g.update((e["sha256"] + "\n").encode())
        g.update((str(e["size"]) + "\n").encode())
    return g.hexdigest()


def verify_zip(
    zip_path: Path,
    sig_path: Path | None = None,
    key_ref: str | None = None,
    strict: bool = True,
) -> tuple[bool, dict]:
    """
    Verify a pack artifact ZIP file.

    Args:
        zip_path: Path to the ZIP file to verify
        sig_path: Optional path to signature file
        key_ref: Optional key reference for cosign verification
        strict: Whether to fail on any verification error

    Returns:
        Tuple of (success, report_dict)
    """
    report = {"zip": str(zip_path), "checks": {}}

    with ZipFile(zip_path, "r") as z:
        names = set(z.namelist())

        # Check for manifest.json
        if "manifest.json" not in names:
            report["checks"]["manifest"] = "missing"
            return (False if strict else True, report)

        # Load and validate manifest
        manifest = json.loads(z.read("manifest.json").decode("utf-8"))

        # Verify files in manifest
        ok_files = True
        for e in manifest.get("files", []):
            if e["path"] not in names:
                ok_files = False
                break
            with z.open(e["path"], "r") as f:
                h = _sha256_stream(f)
            ok_files &= h == e["sha256"]

        report["checks"]["files"] = ok_files

        # Verify Merkle root
        root = _compute_root_from_manifest(manifest)
        report["checks"]["merkle_root_match_manifest"] = root == manifest.get(
            "merkle_root"
        )

        # Check merkle.txt if present
        if "merkle.txt" in names:
            merkle_txt = z.read("merkle.txt").decode("utf-8").strip()
            report["checks"]["merkle_txt_match"] = root == merkle_txt

        # Overall verification result
        ok = all(report["checks"].get(k, True) for k in report["checks"])

    # Verify signature if provided
    if sig_path and sig_path.exists():
        try:
            cmd = f"cosign verify-blob --signature {shlex.quote(str(sig_path))}"
            if key_ref:
                cmd += f" --key {shlex.quote(key_ref)}"
            cmd += f" {shlex.quote(str(zip_path))}"

            subprocess.run(cmd, shell=True, check=True, capture_output=True)
            report["checks"]["signature"] = True
        except Exception as e:
            report["checks"]["signature"] = False
            report["signature_error"] = str(e)
            ok = False if strict else ok

    return (ok, report)


def print_manifest(zip_path: Path) -> dict:
    """
    Extract and return manifest from a pack artifact.

    Args:
        zip_path: Path to the ZIP file

    Returns:
        Manifest dictionary
    """
    with ZipFile(zip_path, "r") as z:
        if "manifest.json" not in z.namelist():
            raise ValueError("No manifest.json found in pack")

        manifest_data = z.read("manifest.json")
        return json.loads(manifest_data.decode("utf-8"))
