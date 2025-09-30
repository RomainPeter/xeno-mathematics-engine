#!/usr/bin/env python3
"""
Tests for manifest validation and verification.
"""
import json
import zipfile

from typer.testing import CliRunner

from pefc.cli import app
from pefc.pack.merkle import build_entries, compute_merkle_root, build_manifest
from pefc.pack.verify import (
    verify_zip,
)


class TestManifestValidation:
    """Test manifest validation functionality."""

    def test_build_manifest_complete(self, tmp_path):
        """Test building complete manifest with all fields."""
        # Create test files
        test_file1 = tmp_path / "test1.txt"
        test_file1.write_text("content1")

        test_file2 = tmp_path / "test2.txt"
        test_file2.write_text("content2")

        # Build entries
        entries = build_entries([(test_file1, "test1.txt"), (test_file2, "test2.txt")])

        # Compute Merkle root
        merkle_root = compute_merkle_root(entries)

        # Build manifest
        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="1.0.0",
            cli_version="0.1.0",
        )

        # Verify manifest structure
        assert manifest["format_version"] == "1.0"
        assert manifest["pack_name"] == "test-pack"
        assert manifest["version"] == "1.0.0"
        assert manifest["merkle_root"] == merkle_root
        assert manifest["file_count"] == 2
        assert manifest["total_size_bytes"] == len("content1") + len("content2")
        assert "builder" in manifest
        assert manifest["builder"]["cli_version"] == "0.1.0"
        assert "host" in manifest["builder"]
        assert len(manifest["files"]) == 2

        # Verify file entries
        for file_info in manifest["files"]:
            assert "path" in file_info
            assert "size" in file_info
            assert "sha256" in file_info
            assert "leaf" in file_info

    def test_manifest_with_signature_info(self, tmp_path):
        """Test manifest with signature information."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # Build entries
        entries = build_entries([(test_file, "test.txt")])
        merkle_root = compute_merkle_root(entries)

        # Build manifest with signature info
        signature_info = {
            "present": True,
            "provider": "cosign",
            "signature_path": "test.txt.sig",
        }

        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="signed-pack",
            version="1.0.0",
            signature_info=signature_info,
        )

        assert manifest["signature"] == signature_info

    def test_verify_zip_with_manifest(self, tmp_path):
        """Test verifying a ZIP with proper manifest."""
        # Create test files
        test_file1 = tmp_path / "file1.txt"
        test_file1.write_text("content1")

        test_file2 = tmp_path / "file2.txt"
        test_file2.write_text("content2")

        # Build entries
        entries = build_entries([(test_file1, "file1.txt"), (test_file2, "file2.txt")])

        merkle_root = compute_merkle_root(entries)
        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="1.0.0",
        )

        # Create ZIP with manifest
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            # Add payload files
            z.writestr("file1.txt", test_file1.read_bytes())
            z.writestr("file2.txt", test_file2.read_bytes())
            # Add manifest and merkle
            z.writestr("manifest.json", json.dumps(manifest, indent=2))
            z.writestr("merkle.txt", merkle_root + "\n")

        # Verify the ZIP
        success, report = verify_zip(zip_path, strict=True)

        assert success
        assert report["checks"]["manifest_valid"] is True
        assert report["checks"]["files_sha256"] is True
        assert report["checks"]["merkle_root"] is True
        assert len(report["errors"]) == 0

    def test_verify_zip_missing_manifest(self, tmp_path):
        """Test verifying ZIP without manifest."""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("file.txt", b"content")

        success, report = verify_zip(zip_path, strict=True)

        assert not success
        assert report["checks"]["manifest_valid"] is False
        assert len(report["errors"]) > 0

    def test_verify_zip_corrupted_file(self, tmp_path):
        """Test verifying ZIP with corrupted file."""
        # Create test files
        test_file = tmp_path / "file.txt"
        test_file.write_text("original content")

        # Build entries
        entries = build_entries([(test_file, "file.txt")])
        merkle_root = compute_merkle_root(entries)
        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="1.0.0",
        )

        # Create ZIP with corrupted file
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            # Add corrupted file (different content)
            z.writestr("file.txt", b"corrupted content")
            z.writestr("manifest.json", json.dumps(manifest, indent=2))
            z.writestr("merkle.txt", merkle_root + "\n")

        # Verify should fail
        success, report = verify_zip(zip_path, strict=True)

        assert not success
        assert report["checks"]["files_sha256"] is False
        assert len(report["errors"]) > 0

    def test_cli_verify_command(self, tmp_path):
        """Test CLI verify command with manifest."""
        # Create test files
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")

        # Build entries and manifest
        entries = build_entries([(test_file, "file.txt")])
        merkle_root = compute_merkle_root(entries)
        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="1.0.0",
        )

        # Create ZIP
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("file.txt", test_file.read_bytes())
            z.writestr("manifest.json", json.dumps(manifest, indent=2))
            z.writestr("merkle.txt", merkle_root + "\n")

        # Test CLI verify
        runner = CliRunner()
        result = runner.invoke(app, ["pack", "verify", "--zip", str(zip_path), "--strict"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["checks"]["manifest_valid"] is True

    def test_cli_manifest_command(self, tmp_path):
        """Test CLI manifest command."""
        # Create test files
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")

        # Build entries and manifest
        entries = build_entries([(test_file, "file.txt")])
        merkle_root = compute_merkle_root(entries)
        manifest = build_manifest(
            entries=entries,
            merkle_root=merkle_root,
            pack_name="test-pack",
            version="1.0.0",
        )

        # Create ZIP
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("file.txt", test_file.read_bytes())
            z.writestr("manifest.json", json.dumps(manifest, indent=2))
            z.writestr("merkle.txt", merkle_root + "\n")

        # Test CLI manifest
        runner = CliRunner()
        result = runner.invoke(app, ["pack", "manifest", "--zip", str(zip_path), "--print"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["format_version"] == "1.0"
        assert output["pack_name"] == "test-pack"
        assert output["merkle_root"] == merkle_root
