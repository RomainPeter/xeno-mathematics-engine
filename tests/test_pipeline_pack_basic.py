#!/usr/bin/env python3
"""
Basic tests for pipeline pack zip functionality.
"""
import json
from pathlib import Path
from unittest.mock import Mock
import pytest

from pefc.pipeline.steps.pack_zip import PackZip
from pefc.pipeline.core import PipelineContext
from pefc.errors import PackBuildError


class TestPipelinePackZipBasic:
    """Test pipeline pack zip functionality with basic approach."""

    def test_pack_zip_step_creation(self, temp_workspace: Path):
        """Test that PackZip step creates a valid ZIP file."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create context
        context = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist",
        )

        # Add files to context
        context.add_file("file1.txt", file1)
        context.add_file("file2.txt", file2)

        # Create PackZip step
        step = PackZip({})

        # Mock config with real values
        context.cfg.pack.pack_name = "test-pack"
        context.cfg.pack.version = "v0.1.0"
        context.cfg.sign.enabled = False
        context.cfg.cli_version = "0.1.0"

        # Run step
        step.run(context)

        # Check that ZIP was created
        zip_files = list((temp_workspace / "dist").glob("*.zip"))
        assert len(zip_files) == 1

        # Check ZIP content
        import zipfile

        with zipfile.ZipFile(zip_files[0], "r") as zf:
            namelist = zf.namelist()
            assert "file1.txt" in namelist
            assert "file2.txt" in namelist
            assert "manifest.json" in namelist
            assert "merkle.txt" in namelist

    def test_zip_content_validation(self, temp_workspace: Path):
        """Test that ZIP contains correct content."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create context
        context = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist",
        )

        # Add files to context
        context.add_file("file1.txt", file1)
        context.add_file("file2.txt", file2)

        # Create PackZip step
        step = PackZip({})

        # Mock config with real values
        context.cfg.pack.pack_name = "test-pack"
        context.cfg.pack.version = "v0.1.0"
        context.cfg.sign.enabled = False
        context.cfg.cli_version = "0.1.0"

        # Run step
        step.run(context)

        # Check ZIP content
        zip_files = list((temp_workspace / "dist").glob("*.zip"))
        assert len(zip_files) == 1

        import zipfile

        with zipfile.ZipFile(zip_files[0], "r") as zf:
            namelist = zf.namelist()
            assert "file1.txt" in namelist
            assert "file2.txt" in namelist
            assert "manifest.json" in namelist
            assert "merkle.txt" in namelist

            # Check file contents
            assert zf.read("file1.txt").decode("utf-8") == "content1"
            assert zf.read("file2.txt").decode("utf-8") == "content2"

            # Check manifest
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            assert manifest["pack_name"] == "test-pack"
            assert manifest["version"] == "v0.1.0"
            assert manifest["format_version"] == "1.0"

            # Check merkle
            merkle_content = zf.read("merkle.txt").decode("utf-8").strip()
            assert merkle_content == manifest["merkle_root"]

    def test_no_duplicate_arcnames(self, temp_workspace: Path):
        """Test that duplicate arcnames are prevented."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create context
        context = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist",
        )

        # Add files with duplicate arcnames
        context.add_file("file1.txt", file1)

        # This should raise an error
        with pytest.raises(PackBuildError, match="duplicate arcname: file1.txt"):
            context.add_file("file1.txt", file2)

    def test_zip_file_integrity(self, temp_workspace: Path):
        """Test ZIP file integrity and structure."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create context
        context = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist",
        )

        # Add files to context
        context.add_file("file1.txt", file1)
        context.add_file("file2.txt", file2)

        # Create PackZip step
        step = PackZip({})

        # Mock config with real values
        context.cfg.pack.pack_name = "test-pack"
        context.cfg.pack.version = "v0.1.0"
        context.cfg.sign.enabled = False
        context.cfg.cli_version = "0.1.0"

        # Run step
        step.run(context)

        # Check ZIP integrity
        zip_files = list((temp_workspace / "dist").glob("*.zip"))
        assert len(zip_files) == 1

        import zipfile

        with zipfile.ZipFile(zip_files[0], "r") as zf:
            # Check that ZIP is valid
            zf.testzip()

            # Check file structure
            namelist = zf.namelist()
            assert len(namelist) == 4  # 2 files + manifest + merkle
            assert "file1.txt" in namelist
            assert "file2.txt" in namelist
            assert "manifest.json" in namelist
            assert "merkle.txt" in namelist

    def test_manifest_schema_compliance(self, temp_workspace: Path):
        """Test that generated manifest complies with schema."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        # Create context
        context = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist",
        )

        # Add files to context
        context.add_file("file1.txt", file1)

        # Create PackZip step
        step = PackZip({})

        # Mock config with real values
        context.cfg.pack.pack_name = "test-pack"
        context.cfg.pack.version = "v0.1.0"
        context.cfg.sign.enabled = False
        context.cfg.cli_version = "0.1.0"

        # Run step
        step.run(context)

        # Check manifest schema compliance
        zip_files = list((temp_workspace / "dist").glob("*.zip"))
        assert len(zip_files) == 1

        import zipfile

        with zipfile.ZipFile(zip_files[0], "r") as zf:
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))

            # Check required fields
            assert "format_version" in manifest
            assert "pack_name" in manifest
            assert "version" in manifest
            assert "built_at" in manifest
            assert "builder" in manifest
            assert "file_count" in manifest
            assert "total_size_bytes" in manifest
            assert "merkle_root" in manifest
            assert "files" in manifest

            # Check format version
            assert manifest["format_version"] == "1.0"

            # Check pack info
            assert manifest["pack_name"] == "test-pack"
            assert manifest["version"] == "v0.1.0"

            # Check file count
            assert manifest["file_count"] == 1

            # Check files
            assert len(manifest["files"]) == 1
            assert manifest["files"][0]["path"] == "file1.txt"

    def test_merkle_root_reproducibility(self, temp_workspace: Path):
        """Test that Merkle root is reproducible for identical content."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create two identical contexts
        context1 = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist1",
        )

        context2 = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist2",
        )

        # Add same files to both contexts
        context1.add_file("file1.txt", file1)
        context1.add_file("file2.txt", file2)

        context2.add_file("file1.txt", file1)
        context2.add_file("file2.txt", file2)

        # Create PackZip steps
        step1 = PackZip({})
        step2 = PackZip({})

        # Mock config with real values
        context1.cfg.pack.pack_name = "test-pack"
        context1.cfg.pack.version = "v0.1.0"
        context1.cfg.sign.enabled = False
        context1.cfg.cli_version = "0.1.0"

        context2.cfg.pack.pack_name = "test-pack"
        context2.cfg.pack.version = "v0.1.0"
        context2.cfg.sign.enabled = False
        context2.cfg.cli_version = "0.1.0"

        # Run PackZip on both
        step1.run(context1)
        step2.run(context2)

        # Check that both ZIPs were created
        zip_files1 = list((temp_workspace / "dist1").glob("*.zip"))
        zip_files2 = list((temp_workspace / "dist2").glob("*.zip"))
        assert len(zip_files1) == 1
        assert len(zip_files2) == 1

        # Check Merkle root reproducibility
        import zipfile

        with zipfile.ZipFile(zip_files1[0], "r") as zf1:
            manifest1 = json.loads(zf1.read("manifest.json").decode("utf-8"))
            merkle1 = zf1.read("merkle.txt").decode("utf-8").strip()

        with zipfile.ZipFile(zip_files2[0], "r") as zf2:
            manifest2 = json.loads(zf2.read("manifest.json").decode("utf-8"))
            merkle2 = zf2.read("merkle.txt").decode("utf-8").strip()

        # Merkle roots should be identical
        assert manifest1["merkle_root"] == manifest2["merkle_root"]
        assert merkle1 == merkle2
        assert merkle1 == manifest1["merkle_root"]
        assert merkle2 == manifest2["merkle_root"]
