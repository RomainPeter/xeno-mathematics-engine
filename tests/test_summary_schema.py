from pathlib import Path
import json
from pefc.summary import build_summary
from pefc.metrics.validator import validate_summary_doc


def write_run(p: Path, run_id: str, group: str, weight: float, metrics: dict):
    p.write_text(
        json.dumps(
            {"run_id": run_id, "group": group, "n_items": weight, "metrics": metrics}
        ),
        encoding="utf-8",
    )


def test_schema_validation_ok(tmp_path: Path):
    """Test that valid summary passes schema validation."""
    write_run(
        tmp_path / "r1.json",
        "r1",
        "baseline",
        10,
        {"coverage_gain": 0.5, "novelty_avg": 0.6, "m": 2},
    )
    write_run(
        tmp_path / "r2.json",
        "r2",
        "active",
        30,
        {"coverage_gain": 0.9, "novelty_avg": 0.4, "m": 3},
    )
    out = tmp_path / "summary.json"
    doc = build_summary([tmp_path], out, validate=False)
    validate_summary_doc(
        doc,
        Path("schema/summary.schema.json"),
        bounded_metrics=["coverage_gain", "novelty_avg"],
    )


def test_bounds_violation(tmp_path: Path):
    """Test that out-of-bounds metrics raise validation error."""
    write_run(tmp_path / "r1.json", "r1", "g", 1, {"novelty_avg": 1.2})
    out = tmp_path / "summary.json"
    doc = build_summary([tmp_path], out, validate=False)
    import pytest

    with pytest.raises(Exception):
        validate_summary_doc(
            doc, Path("schema/summary.schema.json"), bounded_metrics=["novelty_avg"]
        )


def test_schema_validation_integration(tmp_path: Path):
    """Test that build_summary with validate=True works."""
    write_run(
        tmp_path / "r1.json", "r1", "baseline", 10, {"coverage_gain": 0.5, "m": 2}
    )
    write_run(tmp_path / "r2.json", "r2", "active", 30, {"coverage_gain": 0.9, "m": 3})
    out = tmp_path / "summary.json"
    # This should not raise an exception
    build_summary([tmp_path], out, validate=True, bounded_metrics=["coverage_gain"])


def test_required_fields_present(tmp_path: Path):
    """Test that all required fields are present in summary."""
    write_run(tmp_path / "r1.json", "r1", "baseline", 10, {"coverage_gain": 0.5})
    out = tmp_path / "summary.json"
    doc = build_summary([tmp_path], out, validate=False)

    # Check required top-level fields
    assert "version" in doc
    assert "config" in doc
    assert "sources" in doc
    assert "overall" in doc
    assert "by_group" in doc
    assert "runs" in doc

    # Check config fields
    assert "include_aggregates" in doc["config"]
    assert "weight_key" in doc["config"]
    assert "dedup" in doc["config"]

    # Check sources fields
    assert "counts" in doc["sources"]
    assert "ignored_aggregates" in doc["sources"]

    # Check overall structure
    assert "n_runs" in doc["overall"]
    assert "weight_sum" in doc["overall"]
    assert "metrics" in doc["overall"]

    # Check runs structure
    assert len(doc["runs"]) == 1
    run = doc["runs"][0]
    assert "run_id" in run
    assert "group" in run
    assert "weight" in run
    assert "metrics" in run
    assert "source_path" in run
