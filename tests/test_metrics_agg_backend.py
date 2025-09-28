from pathlib import Path
import json
import importlib
import time
import pytest

from pefc.summary import build_summary
from pefc.errors import ValidationError


def _write(p: Path, obj):
    """Helper to write JSON data to file."""
    p.write_text(json.dumps(obj), encoding="utf-8")


def prepare_dataset(tmp: Path):
    """Create a test dataset with multiple runs and groups."""
    _write(
        tmp / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"m": 0.5, "n": 0.2}},
    )
    _write(
        tmp / "r2.json",
        {"run_id": "r2", "group": "g1", "n_items": 30, "metrics": {"m": 0.9, "n": 0.6}},
    )
    _write(
        tmp / "r3.json",
        {"run_id": "r3", "group": "g2", "n_items": 60, "metrics": {"m": 0.4, "n": 0.8}},
    )
    return tmp


def test_equivalence_backends(tmp_path: Path):
    """Test that all backends produce equivalent results."""
    d = prepare_dataset(tmp_path)
    out = tmp_path / "summary.json"

    # python fallback
    res_py = build_summary([d], out, prefer_backend="python")

    # pandas if available
    if importlib.util.find_spec("pandas"):
        res_pd = build_summary([d], out, prefer_backend="pandas")
        assert res_pd["overall"]["metrics"] == res_py["overall"]["metrics"]
        assert res_pd["by_group"] == res_py["by_group"]

    # polars if available
    if importlib.util.find_spec("polars"):
        res_pl = build_summary([d], out, prefer_backend="polars")
        assert res_pl["overall"]["metrics"] == res_py["overall"]["metrics"]
        assert res_pl["by_group"] == res_py["by_group"]


def test_bounds_validation(tmp_path: Path):
    """Test that bounded metrics validation works correctly."""
    d = tmp_path
    _write(
        d / "r1.json",
        {"run_id": "r1", "group": "g", "n_items": 1, "metrics": {"coverage_gain": 1.1}},
    )

    with pytest.raises(ValidationError):
        build_summary([d], d / "summary.json", bounded_metrics=["coverage_gain"])


def test_bounds_validation_valid(tmp_path: Path):
    """Test that valid bounded metrics pass validation."""
    d = tmp_path
    _write(
        d / "r1.json",
        {"run_id": "r1", "group": "g", "n_items": 1, "metrics": {"coverage_gain": 0.8}},
    )

    # Should not raise
    result = build_summary([d], d / "summary.json", bounded_metrics=["coverage_gain"])
    assert result["overall"]["metrics"]["coverage_gain"] == 0.8


def test_perf_sanity_python(tmp_path: Path):
    """Test performance with large dataset using Python backend."""
    # micro bench: 1000 runs should aggregate quickly in python fallback
    for i in range(1000):
        _write(
            tmp_path / f"r{i}.json",
            {
                "run_id": f"r{i}",
                "group": f"g{i % 5}",
                "n_items": 1,
                "metrics": {"m": (i % 100) / 100},
            },
        )

    t0 = time.time()
    res = build_summary([tmp_path], tmp_path / "summary.json", prefer_backend="python")
    dt = time.time() - t0

    assert res["overall"]["n_runs"] == 1000
    assert dt < 10.0  # borne indicative; backend Pandas/Polars sera bien plus rapide


def test_backend_auto_detection(tmp_path: Path):
    """Test that backend auto-detection works."""
    d = prepare_dataset(tmp_path)
    out = tmp_path / "summary.json"

    # Should work without specifying backend
    result = build_summary([d], out)
    assert "backend" in result["config"]
    assert result["overall"]["n_runs"] == 3


def test_weighted_aggregation(tmp_path: Path):
    """Test that weighted aggregation works correctly."""
    d = tmp_path
    # Two runs with different weights
    _write(
        d / "r1.json",
        {"run_id": "r1", "group": "g", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        d / "r2.json",
        {"run_id": "r2", "group": "g", "n_items": 30, "metrics": {"score": 0.9}},
    )

    result = build_summary([d], d / "summary.json", prefer_backend="python")

    # Weighted average: (10*0.5 + 30*0.9) / (10+30) = 32/40 = 0.8
    assert abs(result["overall"]["metrics"]["score"] - 0.8) < 1e-9
    assert result["overall"]["weight_sum"] == 40.0


def test_common_keys_intersection(tmp_path: Path):
    """Test that only common metric keys are used."""
    d = tmp_path
    _write(
        d / "r1.json",
        {"run_id": "r1", "group": "g", "n_items": 1, "metrics": {"a": 0.5, "b": 0.3}},
    )
    _write(
        d / "r2.json",
        {"run_id": "r2", "group": "g", "n_items": 1, "metrics": {"a": 0.7, "c": 0.9}},
    )

    result = build_summary([d], d / "summary.json", prefer_backend="python")

    # Only 'a' should be in the result (common key)
    assert "a" in result["overall"]["metrics"]
    assert "b" not in result["overall"]["metrics"]
    assert "c" not in result["overall"]["metrics"]


def test_empty_dataset(tmp_path: Path):
    """Test handling of empty dataset."""
    d = tmp_path
    d.mkdir(exist_ok=True)

    result = build_summary([d], d / "summary.json", prefer_backend="python")

    assert result["overall"]["n_runs"] == 0
    assert result["overall"]["weight_sum"] == 0.0
    assert result["overall"]["metrics"] == {}
    assert result["by_group"] == {}


def test_schema_validation(tmp_path: Path):
    """Test JSON schema validation if schema is provided."""
    d = prepare_dataset(tmp_path)

    # Create a minimal schema
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["version", "overall"],
        "properties": {"version": {"type": "string"}, "overall": {"type": "object"}},
    }
    schema_path = tmp_path / "schema.json"
    _write(schema_path, schema)

    # Should not raise with valid schema
    result = build_summary([d], d / "summary.json", schema_path=schema_path)
    assert result["version"] is not None
