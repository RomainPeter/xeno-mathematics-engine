from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pefc.events import get_event_bus
from pefc.events import topics as E
from pefc.metrics.engine import aggregate as aggregate_backend
from pefc.metrics.types import RunRecord

logger = logging.getLogger(__name__)


def _detect_source_type(obj: Dict[str, Any]) -> str:
    if isinstance(obj, dict) and ("runs" in obj or obj.get("agg") is True):
        return "aggregate"
    if isinstance(obj, dict) and ("run_id" in obj or "id" in obj or "metrics" in obj):
        return "run"
    return "unknown"


def _extract_run(obj: Dict[str, Any], source_path: str, weight_key: str) -> RunRecord:
    run_id = str(obj.get("run_id") or obj.get("id") or f"anon-{abs(hash(source_path))}")
    group = str(obj.get("group") or obj.get("mode") or "unknown")
    weight = float(obj.get(weight_key) or obj.get("count") or 1.0)
    if "metrics" in obj and isinstance(obj["metrics"], dict):
        metrics = {k: float(v) for k, v in obj["metrics"].items() if isinstance(v, (int, float))}
    else:
        reserved = {"run_id", "id", "group", "mode", "count", "n_items", "agg", "runs"}
        metrics = {
            k: float(v) for k, v in obj.items() if k not in reserved and isinstance(v, (int, float))
        }
    return RunRecord(
        run_id=run_id,
        group=group,
        weight=weight,
        metrics=metrics,
        source_path=source_path,
    )


def load_runs_from_sources(
    sources: List[Path],
    include_aggregates: bool = False,
    weight_key: str = "n_items",
    dedup: str = "first",
) -> Tuple[List[RunRecord], Dict[str, Any]]:
    runs: List[RunRecord] = []
    counts = {"run": 0, "aggregate": 0}
    ignored_aggregates: List[str] = []
    for src in sources:
        files: List[Path]
        if src.is_dir():
            files = sorted(p for p in src.rglob("*.json"))
        else:
            files = [src]
        for f in files:
            try:
                obj = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("metrics: skip unreadable JSON: %s (%s)", f, e)
                continue
            typ = _detect_source_type(obj)
            if typ == "aggregate":
                counts["aggregate"] += 1
                if not include_aggregates:
                    ignored_aggregates.append(str(f))
                    continue
                # Si inclus, on n'injecte pas les runs internes pour éviter double-compte.
                continue
            elif typ == "run":
                counts["run"] += 1
                try:
                    runs.append(_extract_run(obj, str(f), weight_key))
                except Exception as e:
                    logger.warning("metrics: skip invalid run file: %s (%s)", f, e)
            else:
                logger.debug("metrics: unknown JSON shape, skipped: %s", f)
    # Déduplication par run_id
    deduped: Dict[str, RunRecord] = {}
    if dedup == "first":
        for r in runs:
            if r.run_id not in deduped:
                deduped[r.run_id] = r
            else:
                logger.warning(
                    "metrics: duplicate run_id=%s from %s ignored (first kept from %s)",
                    r.run_id,
                    r.source_path,
                    deduped[r.run_id].source_path,
                )
    else:  # last
        for r in runs:
            if r.run_id in deduped:
                logger.warning(
                    "metrics: duplicate run_id=%s replaced: %s -> %s",
                    r.run_id,
                    deduped[r.run_id].source_path,
                    r.source_path,
                )
            deduped[r.run_id] = r
    final_runs = list(deduped.values())
    meta = {"counts": counts, "ignored_aggregates": ignored_aggregates}
    return final_runs, meta


# Legacy function kept for backward compatibility
def aggregate_runs(runs: List[RunRecord]) -> Dict[str, Any]:
    """Legacy aggregation function - use pefc.metrics.engine.aggregate instead."""
    return aggregate_backend(runs, prefer_backend="python")


def _validate_bounds(result: Dict[str, Any], bounded_metrics: List[str]) -> None:
    """Validate that bounded metrics are within [0,1] range."""
    if not bounded_metrics:
        return

    def _check(metrics: Dict[str, float], where: str):
        for k in bounded_metrics:
            if k in metrics:
                v = metrics[k]
                if not (0.0 <= v <= 1.0):
                    raise ValueError(f"metric {k} out of [0,1] in {where}: {v}")

    _check(result["overall"]["metrics"], "overall")
    for g, obj in result["by_group"].items():
        _check(obj["metrics"], f"by_group[{g}]")


def _validate_schema_if_any(doc: Dict[str, Any], schema_path: Optional[Path]) -> None:
    """Validate against JSON schema if available."""
    if not schema_path:
        return
    try:
        import json as _json

        import fastjsonschema
    except Exception:
        logger.warning("schema validation skipped (fastjsonschema not available)")
        return

    sch = _json.loads(Path(schema_path).read_text(encoding="utf-8"))
    validate = fastjsonschema.compile(sch)
    validate(doc)


def build_summary(
    sources: List[Path],
    out_path: Path,
    include_aggregates: bool = False,
    weight_key: str = "n_items",
    dedup: str = "first",
    version: str = "0.1.0",
    prefer_backend: str | None = None,
    bounded_metrics: Optional[List[str]] = None,
    schema_path: Optional[Path] = None,
    provider=None,
) -> Dict[str, Any]:
    """
    Build summary with optimized aggregation backends.

    Args:
        sources: List of source paths for metrics
        out_path: Output path for summary.json
        include_aggregates: Whether to include aggregate data
        weight_key: Key to use for weighting
        dedup: Deduplication strategy
        version: Version string
        prefer_backend: Preferred backend (polars, pandas, python)
        bounded_metrics: Metrics that should be bounded [0,1]
        schema_path: Path to JSON schema for validation

    Returns:
        Summary dictionary
    """
    from pefc.errors import ValidationError  # T07

    if provider is not None:
        from pefc.metrics.parse import provider_to_runs

        runs, meta = provider_to_runs(provider, include_aggregates, weight_key, dedup)
    else:
        runs, meta = load_runs_from_sources(
            sources,
            include_aggregates=include_aggregates,
            weight_key=weight_key,
            dedup=dedup,
        )
    aggs = aggregate_backend(runs, prefer_backend)
    result = {
        "version": version,
        "config": {
            "include_aggregates": include_aggregates,
            "weight_key": weight_key,
            "dedup": dedup,
            "backend": prefer_backend,
        },
        "sources": meta,
        "overall": aggs["overall"],
        "by_group": aggs["by_group"],
        "runs": [
            {
                "run_id": r.run_id,
                "group": r.group,
                "weight": r.weight,
                "metrics": r.metrics,
                "source_path": r.source_path,
            }
            for r in runs
        ],
    }

    try:
        _validate_bounds(result, bounded_metrics or [])
        _validate_schema_if_any(result, schema_path)
    except Exception as e:
        raise ValidationError(str(e))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(
        "summary.json written: %s (backend=%s, runs=%d)",
        out_path,
        prefer_backend,
        len(runs),
    )

    # Emit metrics summary built event
    bus = get_event_bus()
    bus.emit(
        E.METRICS_SUMMARY_BUILT,
        out_path=str(out_path),
        runs=len(runs),
        version=version,
    )

    return result
