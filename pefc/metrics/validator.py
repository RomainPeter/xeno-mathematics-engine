from __future__ import annotations
from pathlib import Path
from typing import Iterable, Optional
import json
import math

try:
    import fastjsonschema as fjs

    HAVE_FJS = True
except Exception:
    from jsonschema import Draft202012Validator

    HAVE_FJS = False

DEFAULT_BOUNDED = {"coverage_gain", "novelty_avg"}


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compile_validator(schema: dict):
    if HAVE_FJS:
        return fjs.compile(schema)
    return Draft202012Validator(schema)


def validate_jsonschema(validator, doc: dict):
    if HAVE_FJS:
        validator(doc)
    else:
        errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
        if errors:
            msg = "; ".join(f"{'/'.join(map(str,e.path))}: {e.message}" for e in errors)
            raise ValueError(f"summary schema validation failed: {msg}")


def is_bounded_metric(name: str, bounded: Optional[set[str]] = None) -> bool:
    if bounded and name in bounded:
        return True
    suffixes = ("_avg", "_mean", "_rate", "_score")
    if name.endswith(suffixes):
        return True
    if name in DEFAULT_BOUNDED:
        return True
    return False


def validate_bounds(summary: dict, bounded: Optional[Iterable[str]] = None):
    bounded_set = set(bounded or [])

    def check_map(metrics: dict, ctx: str):
        for k, v in metrics.items():
            if is_bounded_metric(k, bounded_set):
                if not (0.0 - 1e-12 <= float(v) <= 1.0 + 1e-12):
                    raise ValueError(f"metric {k} out of bounds [0,1] in {ctx}: {v}")

    check_map(summary["overall"]["metrics"], "overall")
    for g, blk in summary["by_group"].items():
        check_map(blk["metrics"], f"by_group[{g}]")
    for r in summary["runs"]:
        check_map(r["metrics"], f"run[{r['run_id']}]")


def validate_coherence(summary: dict, eps: float = 1e-9):
    runs = summary.get("runs", [])
    if not runs:
        return
    # Intersection des clés
    keys = set(runs[0]["metrics"].keys())
    for r in runs[1:]:
        keys &= set(r["metrics"].keys())
    wsum = sum(float(r["weight"]) for r in runs) or 1.0
    recomputed = {
        k: sum(float(r["weight"]) * float(r["metrics"][k]) for r in runs) / wsum
        for k in keys
    }
    for k, v in recomputed.items():
        v0 = float(summary["overall"]["metrics"].get(k, v))
        if math.isnan(v) or math.isnan(v0):
            continue
        if abs(v - v0) > eps:
            raise ValueError(
                f"incoherent overall.metrics[{k}]: got {v0}, expected {v} (eps={eps})"
            )


def validate_summary_doc(
    doc: dict, schema_path: Path, bounded_metrics: Optional[Iterable[str]] = None
):
    schema = load_schema(schema_path)
    validator = compile_validator(schema)
    validate_jsonschema(validator, doc)
    validate_bounds(doc, bounded_metrics)
    validate_coherence(doc)
