#!/usr/bin/env python3
"""
Tests for PEFC CLI pack operations.
"""
import json
import zipfile
from unittest.mock import Mock

from typer.testing import CliRunner

from pefc.cli import app


class TestPackBuild:
    """Test pack build command."""

    def test_pack_build_smoke(self, tmp_path, monkeypatch):
        """Test pack build with minimal setup."""
        # Mock all dependencies
        monkeypatch.setattr(
            "pefc.pipeline.core.PipelineRunner.execute", lambda self, steps: 0
        )
        monkeypatch.setattr("pefc.pipeline.loader.load_pipeline", lambda path: [])
        monkeypatch.setattr("pefc.config.loader.load_config", lambda path=None: Mock())
        monkeypatch.setattr("pefc.logging.init_logging", lambda **kwargs: None)
        monkeypatch.setattr("pefc.events.get_event_bus", lambda: Mock())

        runner = CliRunner()
        result = runner.invoke(app, ["pack", "build"])

        # Should succeed with mocked dependencies
        assert result.exit_code == 0

    def test_pack_build_with_strict(self, tmp_path, monkeypatch):
        """Test pack build with strict mode."""
        # Mock PipelineRunner.execute to return success
        monkeypatch.setattr(
            "pefc.pipeline.core.PipelineRunner.execute", lambda self, steps: 0
        )

        # Mock load_pipeline
        monkeypatch.setattr("pefc.pipeline.loader.load_pipeline", lambda path: [])

        # Mock load_config
        mock_config = Mock()
        mock_config.pack.out_dir = str(tmp_path)
        monkeypatch.setattr(
            "pefc.config.loader.load_config", lambda path=None: mock_config
        )

        runner = CliRunner()
        result = runner.invoke(app, ["pack", "build", "--strict"])

        assert result.exit_code == 0


class TestPackVerify:
    """Test pack verify command."""

    def test_pack_verify_manifest_merkle(self, tmp_path):
        """Test pack verify with manifest and merkle validation."""
        # Create a test ZIP with manifest and merkle
        zpath = tmp_path / "test.zip"

        # Create test files
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Compute SHA256 of test file
        import hashlib

        sha256_hash = hashlib.sha256(test_file.read_bytes()).hexdigest()

        # Create manifest
        files = [
            {
                "path": "test.txt",
                "size": len(test_file.read_bytes()),
                "sha256": sha256_hash,
            }
        ]

        # Compute Merkle root
        g = hashlib.sha256()
        g.update(b"test.txt\n")
        g.update(sha256_hash.encode() + b"\n")
        g.update(str(len(test_file.read_bytes())).encode() + b"\n")
        merkle_root = g.hexdigest()

        manifest = {"version": "v0.1.0", "files": files, "merkle_root": merkle_root}

        # Create ZIP
        with zipfile.ZipFile(zpath, "w") as z:
            z.writestr("test.txt", test_file.read_bytes())
            z.writestr("manifest.json", json.dumps(manifest))
            z.writestr("merkle.txt", merkle_root + "\n")

        runner = CliRunner()
        result = runner.invoke(app, ["pack", "verify", "--zip", str(zpath), "--strict"])

        assert result.exit_code == 0

        # Parse output JSON
        output = json.loads(result.stdout)
        assert output["checks"]["files"] is True
        assert output["checks"]["merkle_root_match_manifest"] is True
        assert output["checks"]["merkle_txt_match"] is True

    def test_pack_verify_missing_manifest(self, tmp_path):
        """Test pack verify with missing manifest."""
        zpath = tmp_path / "test.zip"

        # Create ZIP without manifest
        with zipfile.ZipFile(zpath, "w") as z:
            z.writestr("test.txt", b"content")

        runner = CliRunner()
        result = runner.invoke(app, ["pack", "verify", "--zip", str(zpath), "--strict"])

        assert result.exit_code == 1

        # Parse output JSON
        output = json.loads(result.stdout)
        assert output["checks"]["manifest"] == "missing"


class TestPackManifest:
    """Test pack manifest command."""

    def test_pack_manifest_print(self, tmp_path):
        """Test pack manifest print."""
        zpath = tmp_path / "test.zip"

        # Create test manifest
        manifest = {
            "version": "v0.1.0",
            "files": [{"path": "test.txt", "size": 0, "sha256": "abc123"}],
            "merkle_root": "def456",
        }

        # Create ZIP
        with zipfile.ZipFile(zpath, "w") as z:
            z.writestr("manifest.json", json.dumps(manifest))

        runner = CliRunner()
        result = runner.invoke(
            app, ["pack", "manifest", "--zip", str(zpath), "--print"]
        )

        assert result.exit_code == 0

        # Parse output JSON
        output = json.loads(result.stdout)
        assert output["version"] == "v0.1.0"
        assert output["merkle_root"] == "def456"

    def test_pack_manifest_save_to_file(self, tmp_path):
        """Test pack manifest save to file."""
        zpath = tmp_path / "test.zip"
        out_path = tmp_path / "manifest.json"

        # Create test manifest
        manifest = {
            "version": "v0.1.0",
            "files": [{"path": "test.txt", "size": 0, "sha256": "abc123"}],
            "merkle_root": "def456",
        }

        # Create ZIP
        with zipfile.ZipFile(zpath, "w") as z:
            z.writestr("manifest.json", json.dumps(manifest))

        runner = CliRunner()
        result = runner.invoke(
            app, ["pack", "manifest", "--zip", str(zpath), "--out", str(out_path)]
        )

        assert result.exit_code == 0
        assert out_path.exists()

        # Verify saved manifest
        saved_manifest = json.loads(out_path.read_text())
        assert saved_manifest["version"] == "v0.1.0"


class TestPackSign:
    """Test pack sign command."""

    def test_pack_sign_cosign(self, tmp_path, monkeypatch):
        """Test pack sign with cosign."""
        artifact_path = tmp_path / "test.zip"
        artifact_path.write_bytes(b"test content")

        # Mock cosign command
        mock_sig_path = tmp_path / "test.zip.sig"
        mock_sig_path.write_text("mock signature")

        def mock_sign_with_cosign(artifact, key_ref=None):
            return mock_sig_path

        monkeypatch.setattr("pefc.pack.signing.sign_with_cosign", mock_sign_with_cosign)

        runner = CliRunner()
        result = runner.invoke(
            app, ["pack", "sign", "--in", str(artifact_path), "--provider", "cosign"]
        )

        assert result.exit_code == 0
        assert str(mock_sig_path) in result.stdout

    def test_pack_sign_unknown_provider(self, tmp_path):
        """Test pack sign with unknown provider."""
        artifact_path = tmp_path / "test.zip"
        artifact_path.write_bytes(b"test content")

        runner = CliRunner()
        result = runner.invoke(
            app, ["pack", "sign", "--in", str(artifact_path), "--provider", "unknown"]
        )

        assert result.exit_code == 2
        assert "Unknown provider" in result.stdout


class TestVersion:
    """Test version command."""

    def test_version_command(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        # Should print version (exact format depends on __version__)
        assert result.stdout.strip() is not None
