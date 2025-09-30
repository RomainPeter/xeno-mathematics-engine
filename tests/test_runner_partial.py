from pathlib import Path
import json
from pefc.runner import run_pack_build, BuildStatus


def write_cfg(tmp: Path, enable_sign: bool, key: str | None):
    """Write a temporary configuration file."""
    y = tmp / "pack.yaml"
    y.write_text(
        f"""
pack: {{ version: v0, pack_name: p, out_dir: "{tmp.as_posix()}", zip_name: "p-{ '{' }version{ '}' }.zip" }}
logging: {{ level: INFO, json: false }}
metrics: {{
  sources: ["{tmp.as_posix()}/metrics/*.json"],
  include_aggregates: false, weight_key: n_items, dedup: first,
  bounded_metrics: ["coverage_gain"], schema_path: "{tmp.as_posix()}/summary.schema.json"
}}
merkle: {{ style: v1, chunk_size: 65536 }}
sign: {{ enabled: {str(enable_sign).lower()}, key_ref: {('"' + key + '"') if key else 'null'}, algorithm: cosign }}
""",
        encoding="utf-8",
    )

    # Create minimal metrics and schema
    (tmp / "metrics").mkdir(exist_ok=True)
    (tmp / "metrics" / "r1.json").write_text(
        json.dumps(
            {
                "run_id": "r1",
                "group": "g",
                "n_items": 1,
                "metrics": {"coverage_gain": 0.5},
            }
        ),
        encoding="utf-8",
    )
    (tmp / "summary.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": [
                    "version",
                    "config",
                    "sources",
                    "overall",
                    "by_group",
                    "runs",
                ],
            }
        ),
        encoding="utf-8",
    )
    return y


def test_success_without_sign(tmp_path: Path):
    """Test successful build without signing."""
    cfg = write_cfg(tmp_path, enable_sign=False, key=None)
    res = run_pack_build(config_path=str(cfg))
    assert res.status == BuildStatus.SUCCESS
    assert res.exit_code == 0
    assert "zip" in res.artifacts


def test_partial_on_signature_error(tmp_path: Path):
    """Test partial success when signature fails but is allowed."""
    cfg = write_cfg(
        tmp_path, enable_sign=True, key=None
    )  # sign enabled but no key -> SignatureError
    res = run_pack_build(config_path=str(cfg), allow_partial=True)
    print(
        f"DEBUG: status={res.status}, exit_code={res.exit_code}, reasons={res.reasons}, errors={res.errors}"
    )
    assert res.status == BuildStatus.PARTIAL
    assert res.exit_code == 10
    assert "zip" in res.artifacts
    assert "Signature step failed" in res.reasons


def test_failure_when_strict_signature(tmp_path: Path):
    """Test failure when signature is required but fails."""
    cfg = write_cfg(tmp_path, enable_sign=True, key=None)
    res = run_pack_build(config_path=str(cfg), allow_partial=False)
    assert res.status == BuildStatus.FAILURE
    assert res.exit_code == 40  # SignatureError mapped -> 40
    assert "zip" in res.artifacts  # Zip was created before signature failed


def test_success_with_valid_signature(tmp_path: Path):
    """Test successful build with valid signature configuration."""
    cfg = write_cfg(tmp_path, enable_sign=True, key="test-key")
    res = run_pack_build(config_path=str(cfg))
    assert res.status == BuildStatus.SUCCESS
    assert res.exit_code == 0
    assert "zip" in res.artifacts


def test_partial_is_success(tmp_path: Path):
    """Test that partial success can be treated as success."""
    cfg = write_cfg(tmp_path, enable_sign=True, key=None)
    res = run_pack_build(config_path=str(cfg), allow_partial=True, partial_is_success=True)
    assert res.status == BuildStatus.SUCCESS  # PARTIAL becomes SUCCESS
    assert res.exit_code == 0  # Exit code becomes 0
    assert "zip" in res.artifacts


def test_config_error(tmp_path: Path):
    """Test handling of configuration errors."""
    # Create invalid config
    invalid_cfg = tmp_path / "invalid.yaml"
    invalid_cfg.write_text("invalid: yaml: content: [", encoding="utf-8")

    res = run_pack_build(config_path=str(invalid_cfg))
    assert res.status == BuildStatus.FAILURE
    assert res.exit_code == 50  # ConfigError


def test_metrics_error(tmp_path: Path):
    """Test handling of metrics errors."""
    # Create config with non-existent metrics source
    cfg = tmp_path / "pack.yaml"
    cfg.write_text(
        f"""
pack: {{ version: v0, pack_name: p, out_dir: "{tmp_path.as_posix()}", zip_name: "p.zip" }}
logging: {{ level: INFO, json: false }}
metrics: {{
  sources: ["{tmp_path.as_posix()}/nonexistent/*.json"],
  include_aggregates: false, weight_key: n_items, dedup: first,
  bounded_metrics: ["coverage_gain"], schema_path: "{tmp_path.as_posix()}/summary.schema.json"
}}
merkle: {{ style: v1, chunk_size: 65536 }}
sign: {{ enabled: false, key_ref: null, algorithm: cosign }}
""",
        encoding="utf-8",
    )

    # Create schema but no metrics
    (tmp_path / "summary.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": [
                    "version",
                    "config",
                    "sources",
                    "overall",
                    "by_group",
                    "runs",
                ],
            }
        ),
        encoding="utf-8",
    )

    res = run_pack_build(config_path=str(cfg))
    assert res.status == BuildStatus.FAILURE
    assert res.exit_code in [60, 99]  # MetricsError or UnexpectedError
