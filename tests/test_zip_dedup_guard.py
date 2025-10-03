#!/usr/bin/env python3
"""
Tests for ZIP deduplication guard functionality.
"""

from pathlib import Path

import pytest

from pefc.errors import PackBuildError
from pefc.pipeline.core import PipelineContext
from pefc.pipeline.steps.pack_zip import PackZip


class TestZipDedupGuard:
    """Test ZIP deduplication guard functionality."""

    def test_pack_zip_no_duplicates(self, temp_workspace: Path):
        """Test PackZip with no duplicate arcnames."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context
        ctx = PipelineContext()
        ctx.add_file("file1.txt", file1)
        ctx.add_file("file2.txt", file2)

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step
        step.run(ctx)

        # Check that ZIP was created
        zip_path = temp_workspace / "test.zip"
        assert zip_path.exists()

        # Check ZIP contents
        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            assert "file1.txt" in namelist
            assert "file2.txt" in namelist
            assert "manifest.json" in namelist
            assert "merkle.txt" in namelist
            assert len(namelist) == 4

    def test_pack_zip_with_duplicates(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with duplicate arcnames
        ctx = PipelineContext()
        ctx.add_file("file1.txt", file1)
        ctx.add_file("file1.txt", file2)  # Duplicate arcname

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: file1.txt"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_different_content(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames but different content."""
        # Create test files with different content
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with duplicate arcnames
        ctx = PipelineContext()
        ctx.add_file("duplicate.txt", file1)
        ctx.add_file("duplicate.txt", file2)  # Duplicate arcname

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: duplicate.txt"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_same_content(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames and same content."""
        # Create test files with same content
        file1 = temp_workspace / "file1.txt"
        file1.write_text("same content")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("same content")

        # Create pipeline context with duplicate arcnames
        ctx = PipelineContext()
        ctx.add_file("duplicate.txt", file1)
        ctx.add_file("duplicate.txt", file2)  # Duplicate arcname

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error (duplicate check happens before content check)
        with pytest.raises(PackBuildError, match="duplicate arcname: duplicate.txt"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_manifest_merkle(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames including manifest.json and merkle.txt."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        # Create pipeline context with duplicate arcnames including manifest/merkle
        ctx = PipelineContext()
        ctx.add_file("file1.txt", file1)
        ctx.add_file("manifest.json", file1)  # Duplicate with manifest
        ctx.add_file("merkle.txt", file1)  # Duplicate with merkle

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: manifest.json"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_case_sensitive(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames case sensitive."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with case-sensitive duplicate arcnames
        ctx = PipelineContext()
        ctx.add_file("File1.txt", file1)
        ctx.add_file("file1.txt", file2)  # Different case, should be allowed

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should succeed (case sensitive)
        step.run(ctx)

        # Check that ZIP was created
        zip_path = temp_workspace / "test.zip"
        assert zip_path.exists()

        # Check ZIP contents
        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            assert "File1.txt" in namelist
            assert "file1.txt" in namelist
            assert "manifest.json" in namelist
            assert "merkle.txt" in namelist

    def test_pack_zip_with_duplicates_path_separator(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with path separators."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with path separator duplicates
        ctx = PipelineContext()
        ctx.add_file("path/file.txt", file1)
        ctx.add_file("path\\file.txt", file2)  # Different path separator, should be allowed

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should succeed (different path separators)
        step.run(ctx)

        # Check that ZIP was created
        zip_path = temp_workspace / "test.zip"
        assert zip_path.exists()

        # Check ZIP contents
        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            assert "path/file.txt" in namelist
            assert "path\\file.txt" in namelist
            assert "manifest.json" in namelist
            assert "merkle.txt" in namelist

    def test_pack_zip_with_duplicates_empty_arcname(self, temp_workspace: Path):
        """Test PackZip with duplicate empty arcnames."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with empty arcnames
        ctx = PipelineContext()
        ctx.add_file("", file1)  # Empty arcname
        ctx.add_file("", file2)  # Duplicate empty arcname

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: "):
            step.run(ctx)

    def test_pack_zip_with_duplicates_none_arcname(self, temp_workspace: Path):
        """Test PackZip with duplicate None arcnames."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with None arcnames
        ctx = PipelineContext()
        ctx.add_file(None, file1)  # None arcname
        ctx.add_file(None, file2)  # Duplicate None arcname

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: None"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_unicode(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with unicode characters."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with unicode duplicates
        ctx = PipelineContext()
        ctx.add_file("fichier.txt", file1)  # French
        ctx.add_file("fichier.txt", file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: fichier.txt"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_special_characters(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with special characters."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with special character duplicates
        ctx = PipelineContext()
        ctx.add_file("file@1.txt", file1)  # Special character
        ctx.add_file("file@1.txt", file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: file@1.txt"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_long_paths(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with long paths."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with long path duplicates
        long_path = "very/long/path/with/many/directories/and/subdirectories/file.txt"
        ctx = PipelineContext()
        ctx.add_file(long_path, file1)
        ctx.add_file(long_path, file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match=f"duplicate arcname: {long_path}"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_whitespace(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with whitespace."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with whitespace duplicates
        ctx = PipelineContext()
        ctx.add_file(" file.txt ", file1)  # Leading/trailing whitespace
        ctx.add_file(" file.txt ", file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname:  file.txt "):
            step.run(ctx)

    def test_pack_zip_with_duplicates_tabs(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with tabs."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with tab duplicates
        ctx = PipelineContext()
        ctx.add_file("\tfile.txt", file1)  # Leading tab
        ctx.add_file("\tfile.txt", file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: \tfile.txt"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_newlines(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with newlines."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with newline duplicates
        ctx = PipelineContext()
        ctx.add_file("file\n.txt", file1)  # Newline in name
        ctx.add_file("file\n.txt", file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: file\n.txt"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_carriage_returns(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with carriage returns."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with carriage return duplicates
        ctx = PipelineContext()
        ctx.add_file("file\r.txt", file1)  # Carriage return in name
        ctx.add_file("file\r.txt", file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: file\r.txt"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_mixed_whitespace(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with mixed whitespace."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with mixed whitespace duplicates
        ctx = PipelineContext()
        ctx.add_file(" file\t.txt ", file1)  # Mixed whitespace
        ctx.add_file(" file\t.txt ", file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname:  file\t.txt "):
            step.run(ctx)

    def test_pack_zip_with_duplicates_unicode_whitespace(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with unicode whitespace."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with unicode whitespace duplicates
        ctx = PipelineContext()
        ctx.add_file("file\u00a0.txt", file1)  # Non-breaking space
        ctx.add_file("file\u00a0.txt", file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: file\u00a0.txt"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_control_characters(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with control characters."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with control character duplicates
        ctx = PipelineContext()
        ctx.add_file("file\x00.txt", file1)  # Null character
        ctx.add_file("file\x00.txt", file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: file\x00.txt"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_high_unicode(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with high unicode characters."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with high unicode duplicates
        ctx = PipelineContext()
        ctx.add_file("file\u1f600.txt", file1)  # Emoji
        ctx.add_file("file\u1f600.txt", file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match="duplicate arcname: file\u1f600.txt"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_very_long_names(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with very long names."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with very long name duplicates
        very_long_name = "a" * 1000  # 1000 character name
        ctx = PipelineContext()
        ctx.add_file(very_long_name, file1)
        ctx.add_file(very_long_name, file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match=f"duplicate arcname: {very_long_name}"):
            step.run(ctx)

    def test_pack_zip_with_duplicates_very_long_paths(self, temp_workspace: Path):
        """Test PackZip with duplicate arcnames with very long paths."""
        # Create test files
        file1 = temp_workspace / "file1.txt"
        file1.write_text("content1")

        file2 = temp_workspace / "file2.txt"
        file2.write_text("content2")

        # Create pipeline context with very long path duplicates
        very_long_path = "/".join(["dir"] * 100) + "/file.txt"  # Very long path
        ctx = PipelineContext()
        ctx.add_file(very_long_path, file1)
        ctx.add_file(very_long_path, file2)  # Duplicate

        # Create PackZip step
        step = PackZip({"out": str(temp_workspace / "test.zip")})

        # Run step - should raise error
        with pytest.raises(PackBuildError, match=f"duplicate arcname: {very_long_path}"):
            step.run(ctx)
