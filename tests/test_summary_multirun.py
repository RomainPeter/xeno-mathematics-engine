from pathlib import Path
import json
from pefc.summary import build_summary


def _write(p: Path, obj):
    p.write_text(json.dumps(obj), encoding="utf-8")


def test_no_double_count_ignores_aggregates(tmp_path: Path):
    d = tmp_path
    _write(
        d / "agg.json",
        {"agg": True, "overall": {"coverage_gain": 0.6}, "runs": [{"run_id": "r1"}]},
    )
    _write(
        d / "r1.json",
        {
            "run_id": "r1",
            "group": "baseline",
            "n_items": 10,
            "metrics": {"coverage_gain": 0.5},
        },
    )
    _write(
        d / "r2.json",
        {
            "run_id": "r2",
            "group": "active",
            "n_items": 30,
            "metrics": {"coverage_gain": 0.9},
        },
    )
    out = d / "summary.json"
    res = build_summary([d], out)
    assert res["overall"]["n_runs"] == 2
    assert abs(res["overall"]["metrics"]["coverage_gain"] - 0.8) < 1e-9
    assert res["sources"]["counts"]["aggregate"] == 1
    assert len(res["sources"]["ignored_aggregates"]) == 1


def test_duplicate_run_id_first_kept(tmp_path: Path):
    d = tmp_path
    _write(
        d / "r1a.json",
        {"run_id": "r1", "group": "baseline", "n_items": 10, "metrics": {"m": 0.0}},
    )
    _write(
        d / "r1b.json",
        {"run_id": "r1", "group": "baseline", "n_items": 10, "metrics": {"m": 1.0}},
    )
    res = build_summary([d], d / "summary.json", dedup="first")
    # first kept -> avg = 0.0
    assert res["runs"][0]["metrics"]["m"] == 0.0
