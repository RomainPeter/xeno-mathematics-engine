from pathlib import Path
import json
from pefc.metrics.providers import JsonMetricsProvider, HistoricalMetricsCache
from pefc.metrics.parse import provider_to_runs


def _write(p: Path, obj):
    """Helper to write JSON data to file."""
    p.write_text(json.dumps(obj), encoding="utf-8")


def test_cache_write_mode(tmp_path: Path):
    """Test cache in write mode."""
    # Create source data
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _write(
        source_dir / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )

    # Create cache
    cache_path = tmp_path / "cache.jsonl"
    inner = JsonMetricsProvider([source_dir])
    cache = HistoricalMetricsCache(inner=inner, path=cache_path, mode="write")

    # Test iteration (should write to cache)
    docs = list(cache.iter_docs())
    assert len(docs) == 1
    assert cache_path.exists()

    # Verify cache content
    cache_content = cache_path.read_text(encoding="utf-8")
    assert "r1.json" in cache_content
    assert "score" in cache_content


def test_cache_read_mode(tmp_path: Path):
    """Test cache in read mode."""
    # Create cache file
    cache_path = tmp_path / "cache.jsonl"
    cache_data = [
        {
            "source_id": "test.json",
            "obj": {
                "run_id": "r1",
                "group": "g1",
                "n_items": 10,
                "metrics": {"score": 0.5},
            },
        },
        {
            "source_id": "test2.json",
            "obj": {
                "run_id": "r2",
                "group": "g2",
                "n_items": 20,
                "metrics": {"score": 0.8},
            },
        },
    ]
    cache_path.write_text("\n".join(json.dumps(rec) for rec in cache_data), encoding="utf-8")

    # Create cache in read mode
    cache = HistoricalMetricsCache(inner=None, path=cache_path, mode="read")

    # Test iteration
    docs = list(cache.iter_docs())
    assert len(docs) == 2
    assert docs[0][0] == "test.json"
    assert docs[1][0] == "test2.json"


def test_cache_rw_mode(tmp_path: Path):
    """Test cache in read-write mode."""
    # Create source data
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _write(
        source_dir / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )

    # Create cache
    cache_path = tmp_path / "cache.jsonl"
    inner = JsonMetricsProvider([source_dir])
    cache = HistoricalMetricsCache(inner=inner, path=cache_path, mode="rw")

    # First run: should read from inner and write to cache
    docs = list(cache.iter_docs())
    assert len(docs) == 1
    assert cache_path.exists()

    # Second run: should read from cache
    cache2 = HistoricalMetricsCache(inner=None, path=cache_path, mode="rw")
    docs2 = list(cache2.iter_docs())
    assert len(docs2) == 1
    assert docs2[0][0] == docs[0][0]


def test_cache_no_inner_write_mode(tmp_path: Path):
    """Test cache in write mode with no inner provider."""
    cache_path = tmp_path / "cache.jsonl"
    cache = HistoricalMetricsCache(inner=None, path=cache_path, mode="write")

    # Should yield no documents
    docs = list(cache.iter_docs())
    assert len(docs) == 0
    assert not cache_path.exists()


def test_cache_no_inner_read_mode(tmp_path: Path):
    """Test cache in read mode with no cache file."""
    cache_path = tmp_path / "cache.jsonl"
    cache = HistoricalMetricsCache(inner=None, path=cache_path, mode="read")

    # Should yield no documents
    docs = list(cache.iter_docs())
    assert len(docs) == 0


def test_cache_describe(tmp_path: Path):
    """Test cache describe method."""
    cache_path = tmp_path / "cache.jsonl"
    cache = HistoricalMetricsCache(inner=None, path=cache_path, mode="rw")

    desc = cache.describe()
    assert desc["kind"] == "cache"
    assert desc["path"] == str(cache_path)
    assert desc["mode"] == "rw"
    assert not desc["has_cache"]

    # Create cache file
    cache_path.write_text("test", encoding="utf-8")
    desc2 = cache.describe()
    assert desc2["has_cache"]


def test_cache_with_provider_to_runs(tmp_path: Path):
    """Test cache with provider_to_runs."""
    # Create source data
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _write(
        source_dir / "r1.json",
        {"run_id": "r1", "group": "g1", "n_items": 10, "metrics": {"score": 0.5}},
    )

    # Create cache
    cache_path = tmp_path / "cache.jsonl"
    inner = JsonMetricsProvider([source_dir])
    cache = HistoricalMetricsCache(inner=inner, path=cache_path, mode="rw")

    # Test with provider_to_runs
    runs, meta = provider_to_runs(
        cache, include_aggregates=False, weight_key="n_items", dedup="first"
    )

    assert len(runs) == 1
    assert runs[0].run_id == "r1"
    assert runs[0].weight == 10.0
    assert meta["counts"]["run"] == 1
