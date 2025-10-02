import json
from pathlib import Path

from pefc.metrics.validator import validate_coherence
from pefc.summary import build_summary


def test_coherence_weighted_average(tmp_path: Path):
    """Test that overall metrics match weighted average of runs."""
    (tmp_path / "r1.json").write_text(
        json.dumps(
            {
                "run_id": "r1",
                "group": "g",
                "n_items": 10,
                "metrics": {"x": 1.0, "y": 0.0},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "r2.json").write_text(
        json.dumps(
            {
                "run_id": "r2",
                "group": "g",
                "n_items": 30,
                "metrics": {"x": 0.0, "y": 1.0},
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "summary.json"
    doc = build_summary([tmp_path], out, validate=False)

    # Check that coherence validation passes for correct data
    validate_coherence(doc, eps=1e-12)

    # Force error by modifying doc
    doc["overall"]["metrics"]["x"] = 0.3
    import pytest

    with pytest.raises(Exception):
        validate_coherence(doc, eps=1e-12)


def test_coherence_empty_runs(tmp_path: Path):
    """Test that coherence validation handles empty runs gracefully."""
    out = tmp_path / "summary.json"
    doc = build_summary([tmp_path], out, validate=False)

    # Should not raise an exception for empty runs
    validate_coherence(doc, eps=1e-12)


def test_coherence_single_run(tmp_path: Path):
    """Test coherence with single run."""
    (tmp_path / "r1.json").write_text(
        json.dumps(
            {
                "run_id": "r1",
                "group": "g",
                "n_items": 10,
                "metrics": {"x": 0.5, "y": 0.8},
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "summary.json"
    doc = build_summary([tmp_path], out, validate=False)

    # Should pass for single run
    validate_coherence(doc, eps=1e-12)

    # Check that overall metrics match the single run
    assert doc["overall"]["metrics"]["x"] == 0.5
    assert doc["overall"]["metrics"]["y"] == 0.8


def test_coherence_different_metrics(tmp_path: Path):
    """Test coherence when runs have different metric sets."""
    (tmp_path / "r1.json").write_text(
        json.dumps(
            {
                "run_id": "r1",
                "group": "g",
                "n_items": 10,
                "metrics": {"x": 1.0, "y": 0.0},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "r2.json").write_text(
        json.dumps(
            {
                "run_id": "r2",
                "group": "g",
                "n_items": 30,
                "metrics": {"x": 0.0, "z": 1.0},
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "summary.json"
    doc = build_summary([tmp_path], out, validate=False)

    # Should pass - only common metrics (x) are validated
    validate_coherence(doc, eps=1e-12)

    # Check that only common metric x is in overall
    assert "x" in doc["overall"]["metrics"]
    # y and z should not be in overall since they're not common to all runs
    assert "y" not in doc["overall"]["metrics"]
    assert "z" not in doc["overall"]["metrics"]


def test_coherence_nan_handling(tmp_path: Path):
    """Test that NaN values are handled gracefully in coherence validation."""
    (tmp_path / "r1.json").write_text(
        json.dumps(
            {
                "run_id": "r1",
                "group": "g",
                "n_items": 10,
                "metrics": {"x": float("nan"), "y": 0.5},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "r2.json").write_text(
        json.dumps(
            {
                "run_id": "r2",
                "group": "g",
                "n_items": 30,
                "metrics": {"x": 0.0, "y": 0.8},
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "summary.json"
    doc = build_summary([tmp_path], out, validate=False)

    # Should not raise an exception even with NaN values
    validate_coherence(doc, eps=1e-12)
