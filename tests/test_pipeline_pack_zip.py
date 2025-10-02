#!/usr/bin/env python3
"""
Tests for pipeline pack ZIP creation and content validation.
"""

import json
import zipfile
from pathlib import Path
from typing import List
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from pefc.cli import app
from pefc.pipeline.core import PipelineContext
from pefc.pipeline.steps.pack_zip import PackZip


class TestPipelinePackZip:
    """Test pipeline pack ZIP creation and content validation."""

    def test_pack_zip_step_creation(self, temp_workspace: Path, sample_files: List[Path]):
        """Test that PackZip step creates a valid ZIP file."""
        # Create context
        context = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist",
        )

        # Add files to context
        for i, file_path in enumerate(sample_files):
            context.add_file(f"file{i + 1}.txt", file_path)

        # Create PackZip step
        step = PackZip({})

        # Mock config
        context.cfg.pack.pack_name = "test-pack"
        context.cfg.pack.version = "v0.1.0"
        context.cfg.sign.enabled = False

        # Run step
        step.run(context)

        # Check that ZIP was created
        zip_files = list(context.out_dir.glob("*.zip"))
        assert len(zip_files) == 1

        zip_path = zip_files[0]
        assert zip_path.exists()

        # Check ZIP contents
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            assert "manifest.json" in names
            assert "merkle.txt" in names

            # Check that all files are present
            for i in range(len(sample_files)):
                assert f"file{i + 1}.txt" in names

    def test_zip_content_validation(self, temp_workspace: Path, sample_files: List[Path]):
        """Test that ZIP contains correct content."""
        context = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist",
        )

        # Add files to context
        for i, file_path in enumerate(sample_files):
            context.add_file(f"file{i + 1}.txt", file_path)

        step = PackZip({})
        context.cfg.pack.pack_name = "test-pack"
        context.cfg.pack.version = "v0.1.0"
        context.cfg.sign.enabled = False

        step.run(context)

        # Get ZIP file
        zip_path = list(context.out_dir.glob("*.zip"))[0]

        with zipfile.ZipFile(zip_path, "r") as zf:
            # Check manifest.json
            manifest_data = zf.read("manifest.json")
            manifest = json.loads(manifest_data.decode("utf-8"))

            assert manifest["format_version"] == "1.0"
            assert manifest["pack_name"] == "test-pack"
            assert manifest["version"] == "v0.1.0"
            assert "built_at" in manifest
            assert "builder" in manifest
            assert "files" in manifest

            # Check merkle.txt
            merkle_data = zf.read("merkle.txt")
            merkle_root = merkle_data.decode("utf-8").strip()
            assert merkle_root == manifest["merkle_root"]

            # Check file contents
            for i, file_path in enumerate(sample_files):
                file_data = zf.read(f"file{i + 1}.txt")
                assert file_data == file_path.read_bytes()

    def test_no_duplicate_arcnames(self, temp_workspace: Path, sample_files: List[Path]):
        """Test that duplicate arcnames are prevented."""
        context = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist",
        )

        # Add files with duplicate arcnames
        context.add_file("file1.txt", sample_files[0])
        context.add_file("file1.txt", sample_files[1])  # Duplicate!

        step = PackZip({})
        context.cfg.pack.pack_name = "test-pack"
        context.cfg.pack.version = "v0.1.0"
        context.cfg.sign.enabled = False

        # Should raise error
        with pytest.raises(Exception):  # PackBuildError
            step.run(context)

    def test_event_bus_integration(
        self, temp_workspace: Path, sample_files: List[Path], mock_event_bus
    ):
        """Test that EventBus events are emitted during pipeline execution."""
        with patch("pefc.events.get_event_bus", return_value=mock_event_bus):
            context = PipelineContext(
                cfg=Mock(),
                work_dir=temp_workspace,
                out_dir=temp_workspace / "dist",
            )

            # Add files to context
            for i, file_path in enumerate(sample_files):
                context.add_file(f"file{i + 1}.txt", file_path)

            step = PackZip({})
            context.cfg.pack.pack_name = "test-pack"
            context.cfg.pack.version = "v0.1.0"
            context.cfg.sign.enabled = False

            step.run(context)

            # Check that events were published
            assert mock_event_bus.publish.called

    def test_manifest_merkle_consistency(self, temp_workspace: Path, sample_files: List[Path]):
        """Test that manifest and merkle are consistent."""
        context = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist",
        )

        # Add files to context
        for i, file_path in enumerate(sample_files):
            context.add_file(f"file{i + 1}.txt", file_path)

        step = PackZip({})
        context.cfg.pack.pack_name = "test-pack"
        context.cfg.pack.version = "v0.1.0"
        context.cfg.sign.enabled = False

        step.run(context)

        # Get ZIP file
        zip_path = list(context.out_dir.glob("*.zip"))[0]

        with zipfile.ZipFile(zip_path, "r") as zf:
            # Load manifest
            manifest_data = zf.read("manifest.json")
            manifest = json.loads(manifest_data.decode("utf-8"))

            # Load merkle.txt
            merkle_data = zf.read("merkle.txt")
            merkle_root = merkle_data.decode("utf-8").strip()

            # Check consistency
            assert manifest["merkle_root"] == merkle_root

            # Verify file hashes in manifest
            for file_info in manifest["files"]:
                if file_info["path"] not in {"manifest.json", "merkle.txt"}:
                    # Check that file exists in ZIP
                    assert file_info["path"] in zf.namelist()

                    # Verify SHA256
                    with zf.open(file_info["path"], "r") as f:
                        import hashlib

                        h = hashlib.sha256()
                        for chunk in iter(lambda: f.read(4096), b""):
                            h.update(chunk)
                        actual_sha256 = h.hexdigest()
                        assert actual_sha256 == file_info["sha256"]

    def test_cli_pack_build(self, temp_workspace: Path, sample_files: List[Path]):
        """Test CLI pack build command."""
        # Create test metrics file
        metrics_file = temp_workspace / "metrics.json"
        metrics_data = [
            {
                "run_id": "test_001",
                "timestamp": "2025-01-01T00:00:00Z",
                "metrics": {
                    "coverage_gain": 0.75,
                    "novelty_avg": 0.85,
                    "n_items": 100,
                },
            }
        ]
        metrics_file.write_text(json.dumps(metrics_data, indent=2))

        # Create test pipeline config
        pipeline_config = {
            "name": "Test Pipeline",
            "steps": [
                {
                    "type": "CollectSeeds",
                    "name": "CollectSeeds",
                    "params": {"sources": [str(metrics_file)]},
                },
                {
                    "type": "ComputeMerkle",
                    "name": "ComputeMerkle",
                    "params": {},
                },
                {
                    "type": "PackZip",
                    "name": "PackZip",
                    "params": {"include_manifest": True, "include_merkle": True},
                },
            ],
        }

        pipeline_file = temp_workspace / "test_pipeline.yaml"
        import yaml

        pipeline_file.write_text(yaml.dump(pipeline_config))

        # Create test config
        config = {
            "pack": {
                "version": "v0.1.0",
                "pack_name": "test-pack",
                "out_dir": str(temp_workspace / "dist"),
                "zip_name": "{pack_name}-{version}.zip",
            },
            "logging": {"level": "INFO", "json_mode": False},
            "metrics": {"sources": [str(metrics_file)]},
            "merkle": {"chunk_size": 65536},
            "sign": {"enabled": False},
            "docs": {"onepager": {"template_path": None, "output_file": "ONEPAGER.md"}},
            "sbom": {"path": None},
            "capabilities": {"allowlist": [], "denylist": [], "registry": []},
            "pipelines": {"default": "test", "defs": {"test": pipeline_config}},
            "profiles": {
                "dev": {
                    "logging": {"level": "DEBUG", "json_mode": True},
                    "sign": {"enabled": False},
                }
            },
        }

        config_file = temp_workspace / "config.yaml"
        config_file.write_text(yaml.dump(config))

        # Run CLI command
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "--config",
                str(config_file),
                "pack",
                "build",
                "--pipeline",
                str(pipeline_file),
                "--no-strict",
            ],
        )

        # Check result
        assert result.exit_code == 0

        # Check that ZIP was created
        zip_files = list((temp_workspace / "dist").glob("*.zip"))
        assert len(zip_files) == 1

        # Check ZIP contents
        with zipfile.ZipFile(zip_files[0], "r") as zf:
            names = zf.namelist()
            assert "manifest.json" in names
            assert "merkle.txt" in names

    def test_pipeline_execution_with_events(
        self, temp_workspace: Path, sample_files: List[Path], memory_log_sink
    ):
        """Test pipeline execution with event logging."""
        # Mock event bus
        with patch("pefc.events.get_event_bus") as mock_get_bus:
            mock_bus = Mock()
            mock_bus.subscribe = Mock()
            mock_bus.publish = Mock()
            mock_get_bus.return_value = mock_bus

            context = PipelineContext(
                cfg=Mock(),
                work_dir=temp_workspace,
                out_dir=temp_workspace / "dist",
            )

            # Add files to context
            for i, file_path in enumerate(sample_files):
                context.add_file(f"file{i + 1}.txt", file_path)

            step = PackZip({})
            context.cfg.pack.pack_name = "test-pack"
            context.cfg.pack.version = "v0.1.0"
            context.cfg.sign.enabled = False

            step.run(context)

            # Check that events were published
            assert mock_bus.publish.called

    def test_zip_file_integrity(self, temp_workspace: Path, sample_files: List[Path]):
        """Test ZIP file integrity and structure."""
        context = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist",
        )

        # Add files to context
        for i, file_path in enumerate(sample_files):
            context.add_file(f"file{i + 1}.txt", file_path)

        step = PackZip({})
        context.cfg.pack.pack_name = "test-pack"
        context.cfg.pack.version = "v0.1.0"
        context.cfg.sign.enabled = False

        step.run(context)

        # Get ZIP file
        zip_path = list(context.out_dir.glob("*.zip"))[0]

        # Test ZIP integrity
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Test that ZIP is not corrupted
            zf.testzip()

            # Check that all files are readable
            for name in zf.namelist():
                with zf.open(name, "r") as f:
                    # Should be able to read without errors
                    f.read()

    def test_manifest_schema_compliance(self, temp_workspace: Path, sample_files: List[Path]):
        """Test that generated manifest complies with schema."""
        context = PipelineContext(
            cfg=Mock(),
            work_dir=temp_workspace,
            out_dir=temp_workspace / "dist",
        )

        # Add files to context
        for i, file_path in enumerate(sample_files):
            context.add_file(f"file{i + 1}.txt", file_path)

        step = PackZip({})
        context.cfg.pack.pack_name = "test-pack"
        context.cfg.pack.version = "v0.1.0"
        context.cfg.sign.enabled = False

        step.run(context)

        # Get ZIP file
        zip_path = list(context.out_dir.glob("*.zip"))[0]

        with zipfile.ZipFile(zip_path, "r") as zf:
            # Load manifest
            manifest_data = zf.read("manifest.json")
            manifest = json.loads(manifest_data.decode("utf-8"))

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

            # Check builder structure
            assert "cli_version" in manifest["builder"]
            assert "host" in manifest["builder"]

            # Check files structure
            for file_info in manifest["files"]:
                file_required_fields = ["path", "size", "sha256", "leaf"]
                for field in file_required_fields:
                    assert field in file_info, f"Missing file field: {field}"

    def test_merkle_root_reproducibility(self, temp_workspace: Path, sample_files: List[Path]):
        """Test that Merkle root is reproducible for identical content."""
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
        for i, file_path in enumerate(sample_files):
            context1.add_file(f"file{i + 1}.txt", file_path)
            context2.add_file(f"file{i + 1}.txt", file_path)

        # Run PackZip on both
        step1 = PackZip({})
        step2 = PackZip({})

        context1.cfg.pack.pack_name = "test-pack"
        context1.cfg.pack.version = "v0.1.0"
        context1.cfg.sign.enabled = False

        context2.cfg.pack.pack_name = "test-pack"
        context2.cfg.pack.version = "v0.1.0"
        context2.cfg.sign.enabled = False

        step1.run(context1)
        step2.run(context2)

        # Get both ZIP files
        zip1 = list(context1.out_dir.glob("*.zip"))[0]
        zip2 = list(context2.out_dir.glob("*.zip"))[0]

        # Load manifests
        with zipfile.ZipFile(zip1, "r") as zf1:
            manifest1 = json.loads(zf1.read("manifest.json").decode("utf-8"))

        with zipfile.ZipFile(zip2, "r") as zf2:
            manifest2 = json.loads(zf2.read("manifest.json").decode("utf-8"))

        # Merkle roots should be identical
        assert manifest1["merkle_root"] == manifest2["merkle_root"]
