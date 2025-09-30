#!/usr/bin/env python
import json
import os
import sys
import time
import subprocess
import statistics

ROOT = "spec_pack"
DEC = f"{ROOT}/samples/decisions.jsonl"
EVI = f"{ROOT}/samples/evidence.jsonl"
JRN = f"{ROOT}/samples/journal.ndjson"
ANF = f"{ROOT}/ambition/ambition.json"
MET = f"{ROOT}/metrics.json"
GRAPH = f"{ROOT}/trace.graph.json"


def load_ndjson(p):
    if not os.path.exists(p):
        return []
    with open(p, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def load_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def run_s1():
    try:
        p = subprocess.run(
            ["python", "spec_pack/tools/verify.py", "--s1"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        ok = p.returncode == 0
        details = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {"S1_pass": ok}
        return ok, details
    except Exception:
        return False, {"S1_pass": False}


def get_k(anf):
    try:
        for g in anf.get("guarantees", []):
            if g.get("id") == "G-4":
                k = g.get("params", {}).get("K", 10)
                return int(k)
    except Exception:
        pass
    return 10


def main():
    dec = load_ndjson(DEC)
    evi = load_ndjson(EVI)
    jrn = load_ndjson(JRN)
    anf = load_json(ANF, default={})
    k = get_k(anf)

    tl = [int(d.get("trace_length", 0)) for d in dec if "trace_length" in d]
    avg = statistics.mean(tl) if tl else 0
    mx = max(tl) if tl else 0
    mn = min(tl) if tl else 0
    within_k = mx <= k if tl else True

    s1_ok, s1_details = run_s1()

    metrics = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "k_bound": k,
        "counts": {
            "decisions": len(dec),
            "evidence": len(evi),
            "journal_entries": len(jrn),
        },
        "trace": {
            "avg_length": avg,
            "max_length": mx,
            "min_length": mn,
            "within_k": within_k,
        },
        "s1_pass": bool(s1_ok),
    }
    with open(MET, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Build evidence→decision edges
    nodes = set()
    edges = []
    for d in dec:
        did = d.get("id")
        if not did:
            continue
        nodes.add(("decision", did))
        for evid in d.get("evidence_ids", []):
            nodes.add(("evidence", evid))
            edges.append({"from": evid, "to": did, "type": "supports"})
    graph = {"nodes": [{"id": i, "type": t} for t, i in sorted(nodes)], "edges": edges}
    with open(GRAPH, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    print(json.dumps({"metrics_written": MET, "graph_written": GRAPH}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
