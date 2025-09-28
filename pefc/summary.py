from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class RunRecord:
    run_id: str
    group: str
    weight: float
    metrics: Dict[str, float]
    source_path: str


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
        metrics = {
            k: float(v)
            for k, v in obj["metrics"].items()
            if isinstance(v, (int, float))
        }
    else:
        reserved = {"run_id", "id", "group", "mode", "count", "n_items", "agg", "runs"}
        metrics = {
            k: float(v)
            for k, v in obj.items()
            if k not in reserved and isinstance(v, (int, float))
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


def aggregate_runs(runs: List[RunRecord]) -> Dict[str, Any]:
    if not runs:
        return {
            "overall": {"n_runs": 0, "weight_sum": 0.0, "metrics": {}},
            "by_group": {},
        }
    # Intersection de clés métriques pour éviter NaN
    keys = set(runs[0].metrics.keys())
    for r in runs[1:]:
        keys &= set(r.metrics.keys())
    total_w = sum(r.weight for r in runs) or 1.0
    overall = {
        "n_runs": len(runs),
        "weight_sum": total_w,
        "metrics": {
            k: sum(r.weight * r.metrics[k] for r in runs) / total_w for k in keys
        },
    }
    by_group: Dict[str, Any] = {}
    groups: Dict[str, List[RunRecord]] = {}
    for r in runs:
        groups.setdefault(r.group, []).append(r)
    for g, lst in groups.items():
        w = sum(x.weight for x in lst) or 1.0
        gkeys = set(lst[0].metrics.keys())
        for x in lst[1:]:
            gkeys &= set(x.metrics.keys())
        by_group[g] = {
            "n_runs": len(lst),
            "weight_sum": w,
            "metrics": {
                k: sum(x.weight * x.metrics[k] for x in lst) / w for k in gkeys
            },
        }
    return {"overall": overall, "by_group": by_group}


def build_summary(
    sources: List[Path],
    out_path: Path,
    include_aggregates: bool = False,
    weight_key: str = "n_items",
    dedup: str = "first",
    version: str = "0.1.0",
    validate: bool = False,
    bounded_metrics: Optional[List[str]] = None,
    schema_path: Optional[Path] = None,
) -> Dict[str, Any]:
    runs, meta = load_runs_from_sources(
        sources,
        include_aggregates=include_aggregates,
        weight_key=weight_key,
        dedup=dedup,
    )
    aggs = aggregate_runs(runs)
    result = {
        "version": version,
        "config": {
            "include_aggregates": include_aggregates,
            "weight_key": weight_key,
            "dedup": dedup,
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
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if validate:
        from pefc.metrics.validator import validate_summary_doc

        sp = schema_path or Path("schema/summary.schema.json")
        validate_summary_doc(result, sp, bounded_metrics)
        logger.info("summary.json validated successfully")

    logger.info(
        "summary.json written: %s (runs=%d, aggregates_ignored=%d)",
        out_path,
        len(runs),
        len(meta.get("ignored_aggregates", [])),
    )
    return result
