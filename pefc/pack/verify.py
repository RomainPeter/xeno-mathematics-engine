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
import fastjsonschema


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
    Verify a pack artifact ZIP file with comprehensive validation.

    Args:
        zip_path: Path to the ZIP file to verify
        sig_path: Optional path to signature file
        key_ref: Optional key reference for cosign verification
        strict: Whether to fail on any verification error

    Returns:
        Tuple of (success, report_dict)
    """
    report = {"zip": str(zip_path), "checks": {}, "errors": []}
    overall_success = True

    try:
        # Load and validate manifest
        manifest = load_manifest(zip_path)
        report["checks"]["manifest_valid"] = True

        # Verify files SHA256
        files_ok, files_report = verify_files_sha256(zip_path, manifest)
        report["checks"]["files_sha256"] = files_ok
        report["files_report"] = files_report
        if not files_ok:
            report["errors"].extend(files_report.get("errors", []))
            overall_success = False

        # Verify Merkle root
        merkle_ok, merkle_report = verify_merkle(zip_path, manifest)
        report["checks"]["merkle_root"] = merkle_ok
        report["merkle_report"] = merkle_report
        if not merkle_ok:
            report["errors"].extend(merkle_report.get("errors", []))
            overall_success = False

    except ValueError as e:
        report["checks"]["manifest_valid"] = False
        report["errors"].append(f"Manifest error: {e}")
        overall_success = False
    except Exception as e:
        report["checks"]["manifest_valid"] = False
        report["errors"].append(f"Unexpected error: {e}")
        overall_success = False

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
            report["errors"].append(f"Signature verification failed: {e}")
            overall_success = False

    # Final result
    if strict and not overall_success:
        return (False, report)
    elif not strict and not overall_success:
        # In non-strict mode, return True but with warnings
        report["warnings"] = report.get("warnings", [])
        report["warnings"].extend(report["errors"])
        report["errors"] = []
        return (True, report)
    else:
        return (overall_success, report)


def load_manifest(zip_path: Path) -> dict:
    """
    Load and validate manifest from a pack artifact.

    Args:
        zip_path: Path to the ZIP file

    Returns:
        Manifest dictionary

    Raises:
        ValueError: If manifest is missing or invalid
    """
    with ZipFile(zip_path, "r") as z:
        if "manifest.json" not in z.namelist():
            raise ValueError("No manifest.json found in pack")

        manifest_data = z.read("manifest.json")
        manifest = json.loads(manifest_data.decode("utf-8"))

        # Validate against schema
        try:
            schema_path = (
                Path(__file__).parent.parent.parent / "schema" / "manifest.schema.json"
            )
            with open(schema_path, "r") as f:
                schema = json.load(f)
            fastjsonschema.validate(schema, manifest)
        except Exception as e:
            raise ValueError(f"Manifest validation failed: {e}")

        return manifest


def verify_files_sha256(zip_path: Path, manifest: dict) -> tuple[bool, dict]:
    """
    Verify SHA256 hashes of all files in the manifest.

    Args:
        zip_path: Path to the ZIP file
        manifest: Manifest dictionary

    Returns:
        Tuple of (success, report_dict)
    """
    report = {
        "files_verified": 0,
        "files_total": len(manifest.get("files", [])),
        "errors": [],
    }

    with ZipFile(zip_path, "r") as z:
        for file_info in manifest.get("files", []):
            path = file_info["path"]
            expected_sha256 = file_info["sha256"]

            if path not in z.namelist():
                report["errors"].append(f"File not found in ZIP: {path}")
                continue

            try:
                with z.open(path, "r") as f:
                    actual_sha256 = _sha256_stream(f)

                if actual_sha256 == expected_sha256:
                    report["files_verified"] += 1
                else:
                    report["errors"].append(
                        f"SHA256 mismatch for {path}: expected {expected_sha256}, got {actual_sha256}"
                    )
            except Exception as e:
                report["errors"].append(f"Error reading {path}: {e}")

    success = (
        len(report["errors"]) == 0 and report["files_verified"] == report["files_total"]
    )
    return success, report


def verify_merkle(zip_path: Path, manifest: dict) -> tuple[bool, dict]:
    """
    Verify Merkle root calculation.

    Args:
        zip_path: Path to the ZIP file
        manifest: Manifest dictionary

    Returns:
        Tuple of (success, report_dict)
    """
    report = {"merkle_verified": False, "errors": []}

    try:
        # Recalculate Merkle root from manifest files
        from pefc.pack.merkle import compute_merkle_root, PackEntry

        # Create PackEntry objects from manifest
        entries = []
        for file_info in manifest.get("files", []):
            # Skip manifest.json and merkle.txt from Merkle calculation
            if file_info["path"] in {"manifest.json", "merkle.txt"}:
                continue

            entry = PackEntry(
                arcname=file_info["path"],
                src_path=Path("dummy"),  # Not used for calculation
                size=file_info["size"],
                sha256=file_info["sha256"],
                leaf=file_info["leaf"],
            )
            entries.append(entry)

        # Calculate Merkle root
        calculated_root = compute_merkle_root(entries)
        expected_root = manifest.get("merkle_root")

        if calculated_root == expected_root:
            report["merkle_verified"] = True
        else:
            report["errors"].append(
                f"Merkle root mismatch: expected {expected_root}, got {calculated_root}"
            )

        # Also verify merkle.txt if present
        with ZipFile(zip_path, "r") as z:
            if "merkle.txt" in z.namelist():
                merkle_txt = z.read("merkle.txt").decode("utf-8").strip()
                if merkle_txt != expected_root:
                    report["errors"].append(
                        f"merkle.txt mismatch: expected {expected_root}, got {merkle_txt}"
                    )
                else:
                    report["merkle_txt_verified"] = True

    except Exception as e:
        report["errors"].append(f"Error calculating Merkle root: {e}")

    success = len(report["errors"]) == 0 and report["merkle_verified"]
    return success, report


def print_manifest(zip_path: Path) -> dict:
    """
    Extract and return manifest from a pack artifact.

    Args:
        zip_path: Path to the ZIP file

    Returns:
        Manifest dictionary
    """
    return load_manifest(zip_path)
