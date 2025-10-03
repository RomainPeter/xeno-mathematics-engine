import json
from pathlib import Path

from pefc.metrics.providers import JsonMetricsProvider
from pefc.summary import build_summary


def _write(p: Path, obj):
    """Helper to write JSON data to file."""
    p.write_text(json.dumps(obj), encoding="utf-8")


def test_provider_vs_sources_parity(tmp_path: Path):
    """Test that provider and sources give same results."""
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

    # Test with sources (traditional way)
    sources_result = build_summary(
        sources=[tmp_path],
        out_path=tmp_path / "summary_sources.json",
        include_aggregates=False,
        weight_key="n_items",
        dedup="first",
        version="v0.1.0",
    )

    # Test with provider
    provider = JsonMetricsProvider([tmp_path])
    provider_result = build_summary(
        sources=[],  # Empty sources when using provider
        out_path=tmp_path / "summary_provider.json",
        include_aggregates=False,
        weight_key="n_items",
        dedup="first",
        version="v0.1.0",
        provider=provider,
    )

    # Results should be equivalent
    assert sources_result["overall"]["n_runs"] == provider_result["overall"]["n_runs"]
    assert sources_result["overall"]["weight_sum"] == provider_result["overall"]["weight_sum"]
    assert sources_result["overall"]["metrics"] == provider_result["overall"]["metrics"]
    assert sources_result["by_group"] == provider_result["by_group"]
    assert len(sources_result["runs"]) == len(provider_result["runs"])


def test_provider_vs_sources_with_aggregates(tmp_path: Path):
    """Test provider vs sources with aggregates included."""
    # Create test data with aggregate
    _write(
        tmp_path / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        tmp_path / "agg.json",
        {"agg": True, "overall": {"score": 0.6}, "runs": [{"run_id": "r1"}]},
    )

    # Test with sources
    sources_result = build_summary(
        sources=[tmp_path],
        out_path=tmp_path / "summary_sources.json",
        include_aggregates=True,
        weight_key="n_items",
        dedup="first",
        version="v0.1.0",
    )

    # Test with provider
    provider = JsonMetricsProvider([tmp_path])
    provider_result = build_summary(
        sources=[],
        out_path=tmp_path / "summary_provider.json",
        include_aggregates=True,
        weight_key="n_items",
        dedup="first",
        version="v0.1.0",
        provider=provider,
    )

    # Results should be equivalent
    assert sources_result["overall"]["n_runs"] == provider_result["overall"]["n_runs"]
    # Note: aggregate counts may differ due to different parsing logic
    # The important thing is that the final results are equivalent
    assert sources_result["overall"]["weight_sum"] == provider_result["overall"]["weight_sum"]
    assert sources_result["overall"]["metrics"] == provider_result["overall"]["metrics"]


def test_provider_vs_sources_dedup_strategies(tmp_path: Path):
    """Test provider vs sources with different dedup strategies."""
    # Create duplicate run_id
    _write(
        tmp_path / "r1a.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )
    _write(
        tmp_path / "r1b.json",
        {"run_id": "r1", "group": "g1", "n_items": 20, "metrics": {"score": 0.8}},
    )

    # Test with sources (first)
    sources_result = build_summary(
        sources=[tmp_path],
        out_path=tmp_path / "summary_sources.json",
        include_aggregates=False,
        weight_key="n_items",
        dedup="first",
        version="v0.1.0",
    )

    # Test with provider (first)
    provider = JsonMetricsProvider([tmp_path])
    provider_result = build_summary(
        sources=[],
        out_path=tmp_path / "summary_provider.json",
        include_aggregates=False,
        weight_key="n_items",
        dedup="first",
        version="v0.1.0",
        provider=provider,
    )

    # Results should be equivalent
    assert sources_result["overall"]["n_runs"] == provider_result["overall"]["n_runs"]
    assert sources_result["overall"]["weight_sum"] == provider_result["overall"]["weight_sum"]
    assert sources_result["overall"]["metrics"] == provider_result["overall"]["metrics"]


def test_provider_vs_sources_empty_dataset(tmp_path: Path):
    """Test provider vs sources with empty dataset."""
    # Test with sources (empty directory)
    sources_result = build_summary(
        sources=[tmp_path],
        out_path=tmp_path / "summary_sources.json",
        include_aggregates=False,
        weight_key="n_items",
        dedup="first",
        version="v0.1.0",
    )

    # Test with provider (empty directory)
    provider = JsonMetricsProvider([tmp_path])
    provider_result = build_summary(
        sources=[],
        out_path=tmp_path / "summary_provider.json",
        include_aggregates=False,
        weight_key="n_items",
        dedup="first",
        version="v0.1.0",
        provider=provider,
    )

    # Results should be equivalent
    assert sources_result["overall"]["n_runs"] == provider_result["overall"]["n_runs"]
    assert sources_result["overall"]["weight_sum"] == provider_result["overall"]["weight_sum"]
    assert sources_result["overall"]["metrics"] == provider_result["overall"]["metrics"]
    assert sources_result["by_group"] == provider_result["by_group"]
