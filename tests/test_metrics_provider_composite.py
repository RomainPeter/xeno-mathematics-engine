import json
from pathlib import Path

from pefc.metrics.parse import provider_to_runs
from pefc.metrics.providers import CompositeProvider, JsonMetricsProvider


def _write(p: Path, obj):
    """Helper to write JSON data to file."""
    p.write_text(json.dumps(obj), encoding="utf-8")


def test_composite_provider_basic(tmp_path: Path):
    """Test basic CompositeProvider functionality."""
    # Create two separate directories
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir1.mkdir()
    dir2.mkdir()

    _write(
        dir1 / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        dir2 / "r2.json",
        {"run_id": "r2", "group": "g2", "n_items": 20, "metrics": {"score": 0.8}},
    )

    # Create composite provider
    provider1 = JsonMetricsProvider([dir1])
    provider2 = JsonMetricsProvider([dir2])
    composite = CompositeProvider([provider1, provider2])

    # Test iteration
    docs = list(composite.iter_docs())
    assert len(docs) == 2

    # Test describe
    desc = composite.describe()
    assert desc["kind"] == "composite"
    assert len(desc["children"]) == 2


def test_composite_provider_dedup(tmp_path: Path):
    """Test composite provider with duplicate run_ids."""
    # Create two providers with same run_id
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir1.mkdir()
    dir2.mkdir()

    _write(
        dir1 / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        dir2 / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 20, "metrics": {"score": 0.8}},
    )

    provider1 = JsonMetricsProvider([dir1])
    provider2 = JsonMetricsProvider([dir2])
    composite = CompositeProvider([provider1, provider2])

    # Test deduplication
    runs, meta = provider_to_runs(
        composite, include_aggregates=False, weight_key="n_items", dedup="first"
    )

    assert len(runs) == 1  # Duplicate removed
    assert runs[0].weight == 10.0  # First occurrence kept


def test_composite_provider_order(tmp_path: Path):
    """Test that composite provider maintains order."""
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir1.mkdir()
    dir2.mkdir()

    _write(
        dir1 / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        dir2 / "r2.json",
        {"run_id": "r2", "group": "g2", "n_items": 20, "metrics": {"score": 0.8}},
    )

    provider1 = JsonMetricsProvider([dir1])
    provider2 = JsonMetricsProvider([dir2])
    composite = CompositeProvider([provider1, provider2])

    docs = list(composite.iter_docs())
    assert len(docs) == 2
    # Should get r1 first (from provider1), then r2 (from provider2)
    assert "r1.json" in docs[0][0]
    assert "r2.json" in docs[1][0]


def test_composite_provider_empty(tmp_path: Path):
    """Test composite provider with no providers."""
    composite = CompositeProvider([])

    docs = list(composite.iter_docs())
    assert len(docs) == 0

    desc = composite.describe()
    assert desc["kind"] == "composite"
    assert len(desc["children"]) == 0


def test_composite_provider_nested(tmp_path: Path):
    """Test nested composite providers."""
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir1.mkdir()
    dir2.mkdir()

    _write(
        dir1 / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        dir2 / "r2.json",
        {"run_id": "r2", "group": "g2", "n_items": 20, "metrics": {"score": 0.8}},
    )

    provider1 = JsonMetricsProvider([dir1])
    provider2 = JsonMetricsProvider([dir2])

    # Create nested composite
    inner = CompositeProvider([provider1])
    outer = CompositeProvider([inner, provider2])

    docs = list(outer.iter_docs())
    assert len(docs) == 2

    desc = outer.describe()
    assert desc["kind"] == "composite"
    assert len(desc["children"]) == 2
    assert desc["children"][0]["kind"] == "composite"
    assert desc["children"][1]["kind"] == "json"
