from __future__ import annotations
from typing import Dict, List, Tuple
import logging

from pefc.metrics.types import RunRecord
from pefc.metrics.backends import choose_backend

logger = logging.getLogger(__name__)


def aggregate(
    runs: List[RunRecord], prefer_backend: str | None = None
) -> Dict[str, dict]:
    """
    Aggregate runs using the best available backend.

    Args:
        runs: List of RunRecord objects
        prefer_backend: Preferred backend if available

    Returns:
        Dictionary with 'overall' and 'by_group' aggregation results
    """
    backend = choose_backend(prefer_backend)
    logger.info(f"metrics: using backend={backend} for {len(runs)} runs")

    if backend == "polars":
        return _aggregate_polars(runs)
    elif backend == "pandas":
        return _aggregate_pandas(runs)
    else:
        return _aggregate_python(runs)


def _common_keys(runs: List[RunRecord]) -> List[str]:
    """Find common metric keys across all runs."""
    if not runs:
        return []
    keys = set(runs[0].metrics.keys())
    for r in runs[1:]:
        keys &= set(r.metrics.keys())
    return sorted(keys)


def _reduce_group(
    records: List[RunRecord], keys: List[str]
) -> Tuple[float, Dict[str, float]]:
    """Calculate weighted aggregation for a group of records."""
    wsum = sum(r.weight for r in records) or 1.0
    aggs = {k: sum(r.weight * r.metrics[k] for r in records) / wsum for k in keys}
    return wsum, aggs


def _aggregate_python(runs: List[RunRecord]) -> Dict[str, dict]:
    """Python fallback aggregation."""
    if not runs:
        return {
            "overall": {"n_runs": 0, "weight_sum": 0.0, "metrics": {}},
            "by_group": {},
        }

    keys = _common_keys(runs)
    by_group: Dict[str, List[RunRecord]] = {}
    for r in runs:
        by_group.setdefault(r.group, []).append(r)

    wsum, overall_metrics = _reduce_group(runs, keys)
    by_group_out = {}
    for g, lst in by_group.items():
        gw, gm = _reduce_group(lst, _common_keys(lst))
        by_group_out[g] = {"n_runs": len(lst), "weight_sum": gw, "metrics": gm}

    return {
        "overall": {
            "n_runs": len(runs),
            "weight_sum": wsum,
            "metrics": overall_metrics,
        },
        "by_group": by_group_out,
    }


def _aggregate_pandas(runs: List[RunRecord]) -> Dict[str, dict]:
    """Pandas-based aggregation."""
    import pandas as pd

    if not runs:
        return {
            "overall": {"n_runs": 0, "weight_sum": 0.0, "metrics": {}},
            "by_group": {},
        }

    # Expand to rows: one row per run, metric cols; restrict to common keys
    keys = _common_keys(runs)
    rows = []
    for r in runs:
        row = {"run_id": r.run_id, "group": r.group, "weight": r.weight}
        row.update({k: r.metrics[k] for k in keys})
        rows.append(row)

    df = pd.DataFrame(rows)
    w = df["weight"]
    overall = {
        "n_runs": int(len(df)),
        "weight_sum": float(w.sum()),
        "metrics": {k: float((df[k] * w).sum() / (w.sum() or 1.0)) for k in keys},
    }

    # by group using groupby with weights
    by_group = {}
    for g, sub in df.groupby("group", dropna=False):
        w2 = sub["weight"]
        metrics = {k: float((sub[k] * w2).sum() / (w2.sum() or 1.0)) for k in keys}
        by_group[str(g)] = {
            "n_runs": int(len(sub)),
            "weight_sum": float(w2.sum()),
            "metrics": metrics,
        }

    return {"overall": overall, "by_group": by_group}


def _aggregate_polars(runs: List[RunRecord]) -> Dict[str, dict]:
    """Polars-based aggregation."""
    import polars as pl

    if not runs:
        return {
            "overall": {"n_runs": 0, "weight_sum": 0.0, "metrics": {}},
            "by_group": {},
        }

    keys = _common_keys(runs)
    rows = []
    for r in runs:
        row = {"run_id": r.run_id, "group": r.group, "weight": r.weight}
        row.update({k: r.metrics[k] for k in keys})
        rows.append(row)

    df = pl.DataFrame(rows)
    wsum = float(df["weight"].sum())
    overall_metrics = {
        k: float((df[k] * df["weight"]).sum() / (wsum or 1.0)) for k in keys
    }
    overall = {"n_runs": int(df.height), "weight_sum": wsum, "metrics": overall_metrics}

    by_group = {}
    for g, sub in df.group_by("group", maintain_order=True):
        w2 = float(sub["weight"].sum())
        metrics = {k: float((sub[k] * sub["weight"]).sum() / (w2 or 1.0)) for k in keys}
        by_group[str(g)] = {
            "n_runs": int(sub.height),
            "weight_sum": w2,
            "metrics": metrics,
        }

    return {"overall": overall, "by_group": by_group}
