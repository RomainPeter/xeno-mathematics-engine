from pathlib import Path
import json
import zipfile
import pytest
from pefc.config.loader import get_config
from pefc.pipeline.loader import load_pipeline
from pefc.pipeline.core import PipelineRunner


def _write(p: Path, obj):
    """Helper to write JSON data to file."""
    p.write_text(json.dumps(obj), encoding="utf-8")


def test_pipeline_smoke_builds_zip(tmp_path: Path):
    """Test that pipeline builds a complete zip with all components."""
    # Create synthetic dataset
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()

    _write(
        metrics_dir / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        metrics_dir / "r2.json",
        {"run_id": "r2", "group": "g1", "n_items": 20, "metrics": {"score": 0.8}},
    )

    # Create minimal config
    config_data = {
        "pack": {
            "version": "v0.1.0",
            "pack_name": "test_pack",
            "out_dir": str(tmp_path / "out"),
        },
        "metrics": {
            "sources": [str(metrics_dir)],
            "include_aggregates": False,
            "weight_key": "n_items",
            "dedup": "first",
            "backend": "auto",
            "bounded_metrics": [],
            "schema_path": "schema/summary.schema.json",
            "provider": None,
        },
        "docs": {
            "onepager": {
                "output_file": "ONEPAGER.md",
            }
        },
        "sign": {
            "enabled": False,
        },
    }

    # Write config
    config_path = tmp_path / "config.yaml"
    import yaml

    config_path.write_text(yaml.dump(config_data), encoding="utf-8")

    # Create pipeline YAML
    pipeline_data = {
        "name": "test_pipeline",
        "steps": [
            {"type": "CollectSeeds", "config": {}},
            {"type": "BuildSummary", "config": {}},
            {"type": "RenderDocs", "config": {}},
            {"type": "ComputeMerkle", "config": {}},
            {"type": "PackZip", "config": {"out": "test_pack.zip"}},
        ],
    }
    pipeline_path = tmp_path / "pipeline.yaml"
    pipeline_path.write_text(yaml.dump(pipeline_data), encoding="utf-8")

    # Load and execute pipeline
    cfg = get_config(Path(config_path))
    steps = load_pipeline(pipeline_path)
    runner = PipelineRunner(cfg)

    exit_code = runner.execute(steps)

    # Check results
    assert exit_code == 0  # Success

    # Check zip exists
    zip_path = tmp_path / "out" / "test_pack.zip"
    assert zip_path.exists()

    # Check zip contents
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        assert "summary.json" in names
        assert "manifest.json" in names
        assert "merkle.txt" in names
        assert "ONEPAGER.md" in names


def test_dedup_guard(tmp_path: Path):
    """Test that duplicate arcnames are caught."""
    from pefc.pipeline.core import PipelineContext
    from pefc.errors import PackBuildError

    # Create context with duplicate files
    ctx = PipelineContext(
        cfg=None,
        work_dir=tmp_path,
        out_dir=tmp_path,
    )

    # Add duplicate arcname - should fail immediately
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")
    ctx.add_file("test.txt", test_file)

    with pytest.raises(PackBuildError, match="duplicate arcname"):
        ctx.add_file("test.txt", test_file)  # Duplicate!


def test_sign_partial_success(tmp_path: Path):
    """Test partial success when signing fails."""
    from pefc.pipeline.core import PipelineContext
    from pefc.pipeline.steps.sign_artifact import SignArtifact

    # Create context with zip file
    ctx = PipelineContext(
        cfg=type(
            "Config",
            (),
            {
                "pack": type(
                    "Pack", (), {"sign": type("Sign", (), {"enabled": True})()}
                )()
            },
        )(),
        work_dir=tmp_path,
        out_dir=tmp_path,
    )

    # Add zip file
    zip_file = tmp_path / "test.zip"
    zip_file.write_text("fake zip content")
    ctx.add_file("test.zip", zip_file)

    # Mock cosign to fail
    step = SignArtifact({"method": "cosign", "allow_partial": True})

    # Should not raise exception, but mark as partial
    step.run(ctx)

    assert ctx.status == "partial"
    assert len(ctx.errors) > 0


def test_manifest_integrity(tmp_path: Path):
    """Test that manifest.json has correct Merkle root."""
    from pefc.pipeline.core import PipelineContext
    from pefc.pipeline.steps.compute_merkle import ComputeMerkle

    # Create context with test files
    ctx = PipelineContext(
        cfg=type("Config", (), {"pack": type("Pack", (), {"version": "v0.1.0"})()})(),
        work_dir=tmp_path,
        out_dir=tmp_path,
    )

    # Add test files
    file1 = tmp_path / "file1.txt"
    file1.write_text("content1")
    ctx.add_file("file1.txt", file1)

    file2 = tmp_path / "file2.txt"
    file2.write_text("content2")
    ctx.add_file("file2.txt", file2)

    # Run compute merkle
    step = ComputeMerkle({})
    step.run(ctx)

    # Check manifest exists
    manifest_path = tmp_path / "manifest.json"
    assert manifest_path.exists()

    # Load and verify manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "merkle_root" in manifest
    assert "files" in manifest
    assert len(manifest["files"]) == 2

    # Verify file entries
    file_paths = [f["path"] for f in manifest["files"]]
    assert "file1.txt" in file_paths
    assert "file2.txt" in file_paths

    # Verify Merkle root is not empty
    assert len(manifest["merkle_root"]) == 64  # SHA256 hex length


def test_pipeline_runner_exit_codes(tmp_path: Path):
    """Test pipeline runner exit codes."""
    from pefc.pipeline.core import PipelineRunner, PackStep
    from pefc.errors import SignatureError

    # Test success
    class SuccessStep(PackStep):
        def run(self, ctx):
            pass

    cfg = type("Config", (), {"pack": type("Pack", (), {"out_dir": str(tmp_path)})()})()
    runner = PipelineRunner(cfg)
    steps = [SuccessStep({})]

    exit_code = runner.execute(steps)
    assert exit_code == 0

    # Test partial success (signature error with allow_partial)
    class PartialStep(PackStep):
        def run(self, ctx):
            raise SignatureError("signature failed")

    cfg.pack.sign = type("Sign", (), {"allow_partial": True})()

    runner = PipelineRunner(cfg)
    steps = [PartialStep({})]

    exit_code = runner.execute(steps)
    assert exit_code == 20  # Partial success

    # Test failure
    class FailureStep(PackStep):
        def run(self, ctx):
            raise ValueError("test error")

    cfg.pack.sign.allow_partial = False
    runner = PipelineRunner(cfg)
    steps = [FailureStep({})]

    exit_code = runner.execute(steps)
    assert exit_code == 1  # Failure
