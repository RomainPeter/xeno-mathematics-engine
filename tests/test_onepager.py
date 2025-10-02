import json
from pathlib import Path

from pefc.config.model import (
    DocsConfig,
    LoggingConfig,
    MerkleConfig,
    MetricsConfig,
    OnePagerConfig,
    PackConfig,
    RootConfig,
    SBOMConfig,
)
from pefc.onepager.render import build_onepager


def make_cfg(tmp: Path) -> RootConfig:
    """Create test configuration."""
    return RootConfig(
        pack=PackConfig(
            version="v0.1.0",
            pack_name="test-pack",
            out_dir=tmp.as_posix(),
            zip_name="{pack_name}-{version}.zip",
            include_manifest=True,
            include_merkle=True,
        ),
        logging=LoggingConfig(),
        metrics=MetricsConfig(sources=[tmp.as_posix()], include_aggregates=False),
        merkle=MerkleConfig(),
        docs=DocsConfig(onepager=OnePagerConfig(template_path=None, output_file="ONEPAGER.md")),
        sbom=SBOMConfig(path=None),
    )


def test_onepager_with_manifest_and_summary(tmp_path: Path):
    """Test one-pager generation with manifest and summary."""
    # Create test manifest
    manifest = {
        "version": "1",
        "algorithm": "sha256",
        "pack_version": "v0.1.0",
        "created_at": "2024-01-01T00:00:00Z",
        "file_count": 1,
        "merkle_root": "abcd1234567890",
        "files": [],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    # Create test summary
    summary = {
        "overall": {"n_runs": 1, "weight_sum": 1, "metrics": {"m": 0.5}},
        "by_group": {},
    }
    (tmp_path / "summary.json").write_text(json.dumps(summary), encoding="utf-8")

    cfg = make_cfg(tmp_path)
    out = build_onepager(cfg, tmp_path)
    text = out.read_text(encoding="utf-8")

    assert "Merkle root: abcd1234567890" in text
    assert "Overall: n_runs=1" in text
    assert "m: 0.500000" in text


def test_onepager_reports_missing_artifacts(tmp_path: Path):
    """Test one-pager generation with missing artifacts."""
    cfg = make_cfg(tmp_path)
    out = build_onepager(cfg, tmp_path)
    text = out.read_text(encoding="utf-8")

    assert "Unavailable:" in text  # pour merkle/summary/sbom manquants
    assert "manifest.json not found" in text
    assert "summary.json not found" in text
    assert "No SBOM file detected" in text


def test_onepager_with_sbom(tmp_path: Path):
    """Test one-pager generation with SBOM."""
    # Create test SBOM
    sbom = {
        "components": [
            {"name": "component1", "version": "1.0.0"},
            {"name": "component2", "version": "2.0.0"},
        ]
    }
    (tmp_path / "sbom.json").write_text(json.dumps(sbom), encoding="utf-8")

    cfg = make_cfg(tmp_path)
    out = build_onepager(cfg, tmp_path)
    text = out.read_text(encoding="utf-8")

    assert "Components/Packages: 2" in text


def test_onepager_with_by_group_metrics(tmp_path: Path):
    """Test one-pager generation with by-group metrics."""
    summary = {
        "overall": {"n_runs": 2, "weight_sum": 2, "metrics": {"score": 0.8}},
        "by_group": {
            "group1": {"n_runs": 1, "weight_sum": 1, "metrics": {"score": 0.7}},
            "group2": {"n_runs": 1, "weight_sum": 1, "metrics": {"score": 0.9}},
        },
    }
    (tmp_path / "summary.json").write_text(json.dumps(summary), encoding="utf-8")

    cfg = make_cfg(tmp_path)
    out = build_onepager(cfg, tmp_path)
    text = out.read_text(encoding="utf-8")

    assert "By group:" in text
    assert "group1: n_runs=1" in text
    assert "group2: n_runs=1" in text


def test_onepager_deterministic_output(tmp_path: Path):
    """Test that one-pager output is deterministic (LF newlines)."""
    summary = {
        "overall": {"n_runs": 1, "weight_sum": 1, "metrics": {"test": 0.5}},
        "by_group": {},
    }
    (tmp_path / "summary.json").write_text(json.dumps(summary), encoding="utf-8")

    cfg = make_cfg(tmp_path)
    out = build_onepager(cfg, tmp_path)
    text = out.read_text(encoding="utf-8")

    # Should not contain Windows-style line endings
    assert "\r\n" not in text
    assert "\r" not in text
    # Should contain Unix-style line endings
    assert "\n" in text


def test_onepager_custom_template(tmp_path: Path):
    """Test one-pager generation with custom template."""
    # Create custom template
    template = "Custom: {pack_name} v{pack_version}\nMetrics: {metrics_block}"
    template_path = tmp_path / "custom_template.md"
    template_path.write_text(template, encoding="utf-8")

    # Create config with custom template
    cfg = make_cfg(tmp_path)
    cfg.docs.onepager.template_path = str(template_path)

    out = build_onepager(cfg, tmp_path)
    text = out.read_text(encoding="utf-8")

    assert "Custom: test-pack vv0.1.0" in text
    assert "Metrics:" in text


def test_onepager_invalid_manifest(tmp_path: Path):
    """Test one-pager generation with invalid manifest."""
    # Create invalid manifest (missing required keys)
    invalid_manifest = {"version": "1", "created_at": "2024-01-01T00:00:00Z"}
    (tmp_path / "manifest.json").write_text(json.dumps(invalid_manifest), encoding="utf-8")

    cfg = make_cfg(tmp_path)
    out = build_onepager(cfg, tmp_path)
    text = out.read_text(encoding="utf-8")

    assert "manifest invalid:" in text


def test_onepager_invalid_summary(tmp_path: Path):
    """Test one-pager generation with invalid summary."""
    # Create invalid summary (not JSON)
    (tmp_path / "summary.json").write_text("invalid json", encoding="utf-8")

    cfg = make_cfg(tmp_path)
    out = build_onepager(cfg, tmp_path)
    text = out.read_text(encoding="utf-8")

    assert "summary unreadable:" in text
