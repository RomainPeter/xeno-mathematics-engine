from __future__ import annotations

from typing import Any, Dict, List

from pefc.metrics.types import RunRecord

RESERVED = {"run_id", "id", "group", "mode", "count", "n_items", "agg", "runs"}


def detect_source_type(obj: dict) -> str:
    """Detect the type of metrics source document."""
    if isinstance(obj, dict) and ("runs" in obj or obj.get("agg") is True):
        return "aggregate"
    if isinstance(obj, dict) and ("run_id" in obj or "id" in obj or "metrics" in obj):
        return "run"
    return "unknown"


def extract_run(obj: Dict[str, Any], source_id: str, weight_key: str) -> RunRecord:
    """Extract RunRecord from a metrics document."""
    run_id = str(obj.get("run_id") or obj.get("id") or f"anon-{abs(hash(source_id))}")
    group = str(obj.get("group") or obj.get("mode") or "unknown")
    weight = float(obj.get(weight_key) or obj.get("count") or 1.0)

    if "metrics" in obj and isinstance(obj["metrics"], dict):
        metrics = {k: float(v) for k, v in obj["metrics"].items() if isinstance(v, (int, float))}
    else:
        metrics = {
            k: float(v) for k, v in obj.items() if k not in RESERVED and isinstance(v, (int, float))
        }

    return RunRecord(
        run_id=run_id,
        group=group,
        weight=weight,
        metrics=metrics,
        source_path=source_id,
    )


def provider_to_runs(provider, include_aggregates: bool, weight_key: str, dedup: str):
    """
    Convert provider documents to runs with deduplication.

    Args:
        provider: MetricsProvider instance
        include_aggregates: Whether to include aggregate documents
        weight_key: Key to use for weighting
        dedup: Deduplication strategy ("first" or "last")

    Returns:
        Tuple of (runs, metadata)
    """
    runs: List[RunRecord] = []
    counts = {"run": 0, "aggregate": 0}
    ignored_aggregates: List[str] = []

    for source_id, obj in provider.iter_docs():
        typ = detect_source_type(obj)
        if typ == "aggregate":
            counts["aggregate"] += 1
            if not include_aggregates:
                ignored_aggregates.append(source_id)
                continue
            # agrégats non injectés dans runs par défaut
            continue
        if typ == "run":
            counts["run"] += 1
            try:
                runs.append(extract_run(obj, source_id, weight_key))
            except Exception:
                continue

    # dedup run_id
    deduped = {}
    if dedup == "first":
        for r in runs:
            if r.run_id not in deduped:
                deduped[r.run_id] = r
    else:
        for r in runs:
            deduped[r.run_id] = r

    return list(deduped.values()), {
        "counts": counts,
        "ignored_aggregates": ignored_aggregates,
    }
