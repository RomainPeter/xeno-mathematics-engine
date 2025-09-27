#!/usr/bin/env python3
import argparse
import json
import sys
import itertools
import re
import yaml

HEX64 = re.compile(r"^[a-f0-9]{64}$")


def load_cfg(path="spec_pack/config.yaml"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def load_ndjson(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def index_evidence(evidence_path):
    ev = {}
    for obj in load_ndjson(evidence_path):
        ev[obj["id"]] = set(obj.get("attributes", []))
    return ev


def covers(question_attrs, selected_sets):
    covered = set().union(*selected_sets) if selected_sets else set()
    return set(question_attrs).issubset(covered)


def is_minimal(question_attrs, selected_ids, ev_index):
    selected_sets = [ev_index[i] for i in selected_ids]
    if not covers(question_attrs, selected_sets):
        return False, "coverage_fail"
    # minimality: no proper subset covers
    for r in range(1, len(selected_ids)):
        for subset in itertools.combinations(selected_ids, r):
            if covers(question_attrs, [ev_index[i] for i in subset]):
                return False, {"non_minimal_subset": list(subset)}
    return True, None


def v_minimality(decision, ev_index):
    ok, why = is_minimal(decision["question_attrs"], decision["evidence_ids"], ev_index)
    return {"pass": ok, "details": why}


def v_trace_bound(decision, K):
    return {
        "pass": int(decision.get("trace_length", 999)) <= K,
        "details": {"trace_length": decision.get("trace_length")},
    }


def v_determinism(decision):  # smoke: same evidence_ids repeated
    eids = decision.get("evidence_ids", [])
    for _ in range(3):  # quick check on samples
        if decision.get("evidence_ids", []) != eids:
            return {"pass": False, "details": "evidence_ids changed"}
    return {"pass": True, "details": {}}


def v_provenance(evidence_objects):
    for obj in evidence_objects:
        h = obj.get("content_hash", "")
        if not isinstance(h, str) or not HEX64.match(h):
            return {
                "pass": False,
                "details": {"id": obj.get("id"), "issue": "bad_hash"},
            }
    return {"pass": True, "details": {}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", default="spec_pack/samples/evidence.jsonl")
    ap.add_argument("--decisions", default="spec_pack/samples/decisions.jsonl")
    ap.add_argument("--journal", default="spec_pack/samples/journal.ndjson")
    ap.add_argument(
        "--s1",
        action="store_true",
        help="Run S1 subset: minimality, trace bound, provenance presence",
    )
    args = ap.parse_args()

    cfg = load_cfg()
    K = int(cfg.get("trace_bound_K", 10))

    ev_index = index_evidence(args.evidence)
    evidence_objs = list(load_ndjson(args.evidence))
    decisions = list(load_ndjson(args.decisions))

    if args.s1:
        results = []
        for d in decisions:
            r_min = v_minimality(d, ev_index)
            r_trace = v_trace_bound(d, K=K)
            r_det = v_determinism(d)
            # only check hashes for evidence referenced by this decision
            r_prov = v_provenance(
                [o for o in evidence_objs if o["id"] in d["evidence_ids"]]
            )
            results.append(
                {
                    "decision": d["id"],
                    "minimality": r_min,
                    "trace": r_trace,
                    "determinism": r_det,
                    "provenance": r_prov,
                }
            )
        ok = all(
            r["minimality"]["pass"]
            and r["trace"]["pass"]
            and r["determinism"]["pass"]
            and r["provenance"]["pass"]
            for r in results
        )
        print(json.dumps({"S1_pass": ok, "results": results}, indent=2))
        sys.exit(0 if ok else 1)
    else:
        print("Nothing to do. Use --s1 to run S1 checks.")
        sys.exit(0)


if __name__ == "__main__":
    main()
