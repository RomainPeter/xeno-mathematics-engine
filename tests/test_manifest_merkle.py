#!/usr/bin/env python3
"""
Tests for manifest and Merkle root validation and reproducibility.
"""

import json
import zipfile
from pathlib import Path
from typing import Any, List

import pytest

from pefc.pack.merkle import build_entries, build_manifest, compute_merkle_root
from pefc.pack.verify import (load_manifest, verify_files_sha256,
                              verify_merkle, verify_zip)


class TestManifestMerkle:
    """Test manifest and Merkle root validation and reproducibility."""

    def test_manifest_creation(self, sample_pack_entries: List[Any]):
        """Test manifest creation with all required fields."""
        # Compute Merkle root
        merkle_root = compute_merkle_root(sample_pack_entries)

        # Build manifest
        manifest = build_manifest(
            entries=sample_pack_entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="v0.1.0",
            cli_version="0.1.0",
        )

        # Check required fields
        required_fields = [
            "format_version",
            "pack_name",
            "version",
            "built_at",
            "builder",
            "file_count",
            "total_size_bytes",
            "merkle_root",
            "files",
        ]

        for field in required_fields:
            assert field in manifest, f"Missing required field: {field}"

        # Check specific values
        assert manifest["format_version"] == "1.0"
        assert manifest["pack_name"] == "test-pack"
        assert manifest["version"] == "v0.1.0"
        assert manifest["merkle_root"] == merkle_root
        assert manifest["file_count"] == len(sample_pack_entries)

        # Check builder structure
        assert "cli_version" in manifest["builder"]
        assert "host" in manifest["builder"]
        assert manifest["builder"]["cli_version"] == "0.1.0"

        # Check files structure
        assert len(manifest["files"]) == len(sample_pack_entries)
        for file_info in manifest["files"]:
            file_required_fields = ["path", "size", "sha256", "leaf"]
            for field in file_required_fields:
                assert field in file_info, f"Missing file field: {field}"

    def test_merkle_root_reproducibility(self, sample_files: List[Path]):
        """Test that Merkle root is reproducible for identical content."""
        # Create entries twice
        entries1 = build_entries([(f, f"file{i + 1}.txt") for i, f in enumerate(sample_files)])
        entries2 = build_entries([(f, f"file{i + 1}.txt") for i, f in enumerate(sample_files)])

        # Compute Merkle roots
        root1 = compute_merkle_root(entries1)
        root2 = compute_merkle_root(entries2)

        # Should be identical
        assert root1 == root2

    def test_merkle_root_deterministic_ordering(self, sample_files: List[Path]):
        """Test that Merkle root is deterministic regardless of file order."""
        # Create entries in different orders
        entries1 = build_entries([(f, f"file{i + 1}.txt") for i, f in enumerate(sample_files)])
        entries2 = build_entries(
            [(f, f"file{i + 1}.txt") for i, f in enumerate(reversed(sample_files))]
        )

        # Compute Merkle roots
        root1 = compute_merkle_root(entries1)
        root2 = compute_merkle_root(entries2)

        # Should be identical (ordering should not matter)
        assert root1 == root2

    def test_manifest_merkle_consistency(self, temp_workspace: Path, sample_files: List[Path]):
        """Test that manifest Merkle root matches actual Merkle root."""
        # Create entries
        entries = build_entries([(f, f"file{i + 1}.txt") for i, f in enumerate(sample_files)])
        merkle_root = compute_merkle_root(entries)

        # Build manifest
        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="v0.1.0",
        )

        # Check consistency
        assert manifest["merkle_root"] == merkle_root

        # Check that file hashes in manifest match actual file hashes
        for i, file_info in enumerate(manifest["files"]):
            if file_info["path"] not in {"manifest.json", "merkle.txt"}:
                # Find corresponding entry
                for entry in entries:
                    if entry.arcname == file_info["path"]:
                        assert file_info["sha256"] == entry.sha256
                        assert file_info["leaf"] == entry.leaf
                        assert file_info["size"] == entry.size
                        break

    def test_zip_manifest_verification(self, temp_workspace: Path, sample_files: List[Path]):
        """Test ZIP manifest verification."""
        # Create a ZIP with manifest
        zip_path = temp_workspace / "test.zip"

        # Create entries
        entries = build_entries([(f, f"file{i + 1}.txt") for i, f in enumerate(sample_files)])
        merkle_root = compute_merkle_root(entries)

        # Build manifest
        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="v0.1.0",
        )

        # Create ZIP
        with zipfile.ZipFile(zip_path, "w") as zf:
            # Add files
            for i, file_path in enumerate(sample_files):
                zf.write(file_path, f"file{i + 1}.txt")

            # Add manifest and merkle
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("merkle.txt", merkle_root + "\n")

        # Verify ZIP
        success, report = verify_zip(zip_path, strict=True)

        assert success
        assert report["checks"]["manifest_valid"] is True
        assert report["checks"]["files_sha256"] is True
        assert report["checks"]["merkle_root"] is True

    def test_manifest_schema_validation(self, sample_pack_entries: List[Any]):
        """Test manifest schema validation."""
        # Build manifest
        merkle_root = compute_merkle_root(sample_pack_entries)
        manifest = build_manifest(
            entries=sample_pack_entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="v0.1.0",
        )

        # Load schema
        schema_path = Path("schema/manifest.schema.json")
        if not schema_path.exists():
            pytest.skip("Manifest schema not found")

        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Validate manifest
        import fastjsonschema

        validator = fastjsonschema.compile(schema)

        try:
            validator(manifest)
        except fastjsonschema.JsonSchemaValueException as e:
            pytest.fail(f"Manifest schema validation failed: {e}")

    def test_sha256_verification(self, temp_workspace: Path, sample_files: List[Path]):
        """Test SHA256 verification of files in ZIP."""
        # Create ZIP
        zip_path = temp_workspace / "test.zip"

        entries = build_entries([(f, f"file{i + 1}.txt") for i, f in enumerate(sample_files)])
        merkle_root = compute_merkle_root(entries)

        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="v0.1.0",
        )

        with zipfile.ZipFile(zip_path, "w") as zf:
            for i, file_path in enumerate(sample_files):
                zf.write(file_path, f"file{i + 1}.txt")
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("merkle.txt", merkle_root + "\n")

        # Test SHA256 verification
        success, report = verify_files_sha256(zip_path, manifest)

        assert success
        assert report["files_verified"] == len(sample_files)
        assert report["files_total"] == len(sample_files)
        assert len(report.get("errors", [])) == 0

    def test_merkle_verification(self, temp_workspace: Path, sample_files: List[Path]):
        """Test Merkle root verification."""
        # Create ZIP
        zip_path = temp_workspace / "test.zip"

        entries = build_entries([(f, f"file{i + 1}.txt") for i, f in enumerate(sample_files)])
        merkle_root = compute_merkle_root(entries)

        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="v0.1.0",
        )

        with zipfile.ZipFile(zip_path, "w") as zf:
            for i, file_path in enumerate(sample_files):
                zf.write(file_path, f"file{i + 1}.txt")
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("merkle.txt", merkle_root + "\n")

        # Test Merkle verification
        success, report = verify_merkle(zip_path, manifest)

        assert success
        assert report["merkle_verified"] is True
        assert report["merkle_txt_verified"] is True
        assert len(report.get("errors", [])) == 0

    def test_manifest_loading(self, temp_workspace: Path, sample_files: List[Path]):
        """Test manifest loading from ZIP."""
        # Create ZIP
        zip_path = temp_workspace / "test.zip"

        entries = build_entries([(f, f"file{i + 1}.txt") for i, f in enumerate(sample_files)])
        merkle_root = compute_merkle_root(entries)

        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="v0.1.0",
        )

        with zipfile.ZipFile(zip_path, "w") as zf:
            for i, file_path in enumerate(sample_files):
                zf.write(file_path, f"file{i + 1}.txt")
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("merkle.txt", merkle_root + "\n")

        # Test manifest loading
        loaded_manifest = load_manifest(zip_path)

        assert loaded_manifest == manifest

    def test_corrupted_file_detection(self, temp_workspace: Path, sample_files: List[Path]):
        """Test detection of corrupted files in ZIP."""
        # Create ZIP with corrupted file
        zip_path = temp_workspace / "test.zip"

        entries = build_entries([(f, f"file{i + 1}.txt") for i, f in enumerate(sample_files)])
        merkle_root = compute_merkle_root(entries)

        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="v0.1.0",
        )

        with zipfile.ZipFile(zip_path, "w") as zf:
            # Add corrupted file (different content)
            zf.writestr("file1.txt", b"corrupted content")
            for i, file_path in enumerate(sample_files[1:], 1):
                zf.write(file_path, f"file{i + 1}.txt")
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("merkle.txt", merkle_root + "\n")

        # Test verification (should fail)
        success, report = verify_zip(zip_path, strict=True)

        assert not success
        assert report["checks"]["files_sha256"] is False
        assert len(report["errors"]) > 0

    def test_missing_manifest_detection(self, temp_workspace: Path, sample_files: List[Path]):
        """Test detection of missing manifest in ZIP."""
        # Create ZIP without manifest
        zip_path = temp_workspace / "test.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            for i, file_path in enumerate(sample_files):
                zf.write(file_path, f"file{i + 1}.txt")
            zf.writestr("merkle.txt", "dummy_merkle_root\n")

        # Test verification (should fail)
        success, report = verify_zip(zip_path, strict=True)

        assert not success
        assert report["checks"]["manifest_valid"] is False
        assert len(report["errors"]) > 0

    def test_merkle_txt_consistency(self, temp_workspace: Path, sample_files: List[Path]):
        """Test consistency between manifest.merkle_root and merkle.txt."""
        # Create ZIP
        zip_path = temp_workspace / "test.zip"

        entries = build_entries([(f, f"file{i + 1}.txt") for i, f in enumerate(sample_files)])
        merkle_root = compute_merkle_root(entries)

        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="v0.1.0",
        )

        with zipfile.ZipFile(zip_path, "w") as zf:
            for i, file_path in enumerate(sample_files):
                zf.write(file_path, f"file{i + 1}.txt")
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("merkle.txt", merkle_root + "\n")

        # Test consistency
        with zipfile.ZipFile(zip_path, "r") as zf:
            manifest_data = zf.read("manifest.json")
            manifest = json.loads(manifest_data.decode("utf-8"))

            merkle_txt_data = zf.read("merkle.txt")
            merkle_txt_root = merkle_txt_data.decode("utf-8").strip()

            assert manifest["merkle_root"] == merkle_txt_root

    def test_manifest_excludes_itself_from_merkle(
        self, temp_workspace: Path, sample_files: List[Path]
    ):
        """Test that manifest.json and merkle.txt are excluded from Merkle calculation."""
        # Create entries
        entries = build_entries([(f, f"file{i + 1}.txt") for i, f in enumerate(sample_files)])
        merkle_root = compute_merkle_root(entries)

        # Build manifest
        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="v0.1.0",
        )

        # Check that manifest.json and merkle.txt are not in files list
        file_paths = [f["path"] for f in manifest["files"]]
        assert "manifest.json" not in file_paths
        assert "merkle.txt" not in file_paths

        # Check that total_size_bytes excludes manifest.json and merkle.txt
        expected_size = sum(f["size"] for f in manifest["files"])
        assert manifest["total_size_bytes"] == expected_size

    def test_manifest_reproducibility(self, sample_files: List[Path]):
        """Test that manifest generation is reproducible."""
        # Create entries
        entries = build_entries([(f, f"file{i + 1}.txt") for i, f in enumerate(sample_files)])
        merkle_root = compute_merkle_root(entries)

        # Build manifest twice
        manifest1 = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="v0.1.0",
        )

        manifest2 = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="v0.1.0",
        )

        # Should be identical (except for built_at which may differ)
        assert manifest1["format_version"] == manifest2["format_version"]
        assert manifest1["pack_name"] == manifest2["pack_name"]
        assert manifest1["version"] == manifest2["version"]
        assert manifest1["merkle_root"] == manifest2["merkle_root"]
        assert manifest1["file_count"] == manifest2["file_count"]
        assert manifest1["total_size_bytes"] == manifest2["total_size_bytes"]
        assert manifest1["files"] == manifest2["files"]
        assert manifest1["builder"] == manifest2["builder"]
