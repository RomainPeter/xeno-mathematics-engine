#!/usr/bin/env python3
"""
Debug tests for pipeline pack zip functionality.
"""
from pathlib import Path
from unittest.mock import Mock

from pefc.pipeline.steps.pack_zip import PackZip
from pefc.pipeline.core import PipelineContext


class TestPipelinePackZipDebug:
    """Debug test for pipeline pack zip functionality."""

    def test_pack_zip_debug(self, temp_workspace: Path):
        """Debug test to see what's happening."""
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

        # Debug: Check context state
        print(f"Context files: {context.files}")
        print(f"Context out_dir: {context.out_dir}")
        print(f"Context work_dir: {context.work_dir}")
        print(f"Config pack_name: {context.cfg.pack.pack_name}")
        print(f"Config version: {context.cfg.pack.version}")

        # Run step
        try:
            step.run(context)
            print("Step completed successfully")
        except Exception as e:
            print(f"Step failed with error: {e}")
            import traceback

            traceback.print_exc()

        # Check what was created
        print(f"Files in temp_workspace: {list(temp_workspace.iterdir())}")
        print(
            f"Files in dist: {list((temp_workspace / 'dist').iterdir()) if (temp_workspace / 'dist').exists() else 'dist does not exist'}"
        )

        # Check that ZIP was created
        zip_files = list((temp_workspace / "dist").glob("*.zip"))
        print(f"ZIP files found: {zip_files}")
        assert len(zip_files) == 1
