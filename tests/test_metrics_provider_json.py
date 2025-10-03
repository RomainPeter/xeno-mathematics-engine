import json
from pathlib import Path

from pefc.metrics.parse import provider_to_runs
from pefc.metrics.providers import JsonMetricsProvider
from pefc.summary import build_summary


def _write(p: Path, obj):
    """Helper to write JSON data to file."""
    p.write_text(json.dumps(obj), encoding="utf-8")


def test_json_provider_basic(tmp_path: Path):
    """Test basic JsonMetricsProvider functionality."""
    # Create test data
    _write(
        tmp_path / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        tmp_path / "r2.json",
        {"run_id": "r2", "group": "g1", "n_items": 20, "metrics": {"score": 0.8}},
    )
    _write(
        tmp_path / "r3.json",
        {"run_id": "r3", "group": "g2", "n_items": 30, "metrics": {"score": 0.3}},
    )

    # Test provider
    provider = JsonMetricsProvider([tmp_path])
    docs = list(provider.iter_docs())
    assert len(docs) == 3

    # Test describe
    desc = provider.describe()
    assert desc["kind"] == "json"
    assert str(tmp_path) in desc["paths"]


def test_json_provider_with_subdirs(tmp_path: Path):
    """Test JsonMetricsProvider with subdirectories."""
    # Create subdirectory structure
    (tmp_path / "subdir").mkdir()
    _write(
        tmp_path / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        tmp_path / "subdir" / "r2.json",
        {"run_id": "r2", "group": "g1", "n_items": 20, "metrics": {"score": 0.8}},
    )

    provider = JsonMetricsProvider([tmp_path])
    docs = list(provider.iter_docs())
    assert len(docs) == 2


def test_provider_to_runs(tmp_path: Path):
    """Test provider_to_runs function."""
    _write(
        tmp_path / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        tmp_path / "r2.json",
        {"run_id": "r2", "group": "g1", "n_items": 20, "metrics": {"score": 0.8}},
    )

    provider = JsonMetricsProvider([tmp_path])
    runs, meta = provider_to_runs(
        provider, include_aggregates=False, weight_key="n_items", dedup="first"
    )

    assert len(runs) == 2
    assert meta["counts"]["run"] == 2
    assert meta["counts"]["aggregate"] == 0
    assert runs[0].run_id == "r1"
    assert runs[1].run_id == "r2"


def test_build_summary_with_provider(tmp_path: Path):
    """Test build_summary with provider."""
    _write(
        tmp_path / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        tmp_path / "r2.json",
        {"run_id": "r2", "group": "g1", "n_items": 20, "metrics": {"score": 0.8}},
    )

    provider = JsonMetricsProvider([tmp_path])
    out_path = tmp_path / "summary.json"

    result = build_summary(
        sources=[],  # Empty sources when using provider
        out_path=out_path,
        include_aggregates=False,
        weight_key="n_items",
        dedup="first",
        version="v0.1.0",
        provider=provider,
    )

    assert result["overall"]["n_runs"] == 2
    assert result["overall"]["weight_sum"] == 30.0
    assert "score" in result["overall"]["metrics"]
    assert out_path.exists()


def test_provider_aggregates_ignored(tmp_path: Path):
    """Test that aggregates are ignored by default."""
    _write(
        tmp_path / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        tmp_path / "agg.json",
        {"agg": True, "overall": {"score": 0.6}, "runs": [{"run_id": "r1"}]},
    )

    provider = JsonMetricsProvider([tmp_path])
    runs, meta = provider_to_runs(
        provider, include_aggregates=False, weight_key="n_items", dedup="first"
    )

    assert len(runs) == 1  # Only the run, not the aggregate
    assert meta["counts"]["run"] == 1
    assert meta["counts"]["aggregate"] == 1
    assert len(meta["ignored_aggregates"]) == 1


def test_provider_aggregates_included(tmp_path: Path):
    """Test that aggregates can be included."""
    _write(
        tmp_path / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        tmp_path / "agg.json",
        {"agg": True, "overall": {"score": 0.6}, "runs": [{"run_id": "r1"}]},
    )

    provider = JsonMetricsProvider([tmp_path])
    runs, meta = provider_to_runs(
        provider, include_aggregates=True, weight_key="n_items", dedup="first"
    )

    assert len(runs) == 1  # Still only the run (aggregates don't inject runs)
    assert meta["counts"]["run"] == 1
    assert meta["counts"]["aggregate"] == 1
    assert len(meta["ignored_aggregates"]) == 0


def test_provider_dedup_first(tmp_path: Path):
    """Test deduplication with 'first' strategy."""
    _write(
        tmp_path / "r1a.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        tmp_path / "r1b.json",
        {"run_id": "r1", "group": "g1", "n_items": 20, "metrics": {"score": 0.8}},
    )

    provider = JsonMetricsProvider([tmp_path])
    runs, meta = provider_to_runs(
        provider, include_aggregates=False, weight_key="n_items", dedup="first"
    )

    assert len(runs) == 1
    assert runs[0].weight == 10.0  # First occurrence


def test_provider_dedup_last(tmp_path: Path):
    """Test deduplication with 'last' strategy."""
    _write(
        tmp_path / "r1a.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        tmp_path / "r1b.json",
        {"run_id": "r1", "group": "g1", "n_items": 20, "metrics": {"score": 0.8}},
    )

    provider = JsonMetricsProvider([tmp_path])
    runs, meta = provider_to_runs(
        provider, include_aggregates=False, weight_key="n_items", dedup="last"
    )

    assert len(runs) == 1
    assert runs[0].weight == 20.0  # Last occurrence
