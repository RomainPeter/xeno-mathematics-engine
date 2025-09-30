#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from datetime import datetime

DECISIONS = "spec_pack/samples/decisions.jsonl"
DEC_STAT = "spec_pack/samples/decisions_status.jsonl"
INCIDENTS = "spec_pack/samples/incidents.ndjson"
RETRO = "spec_pack/retro_rules.yaml"


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def parse_iso(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def main():
    decisions = load_jsonl(DECISIONS)
    status = load_jsonl(DEC_STAT)
    incidents = load_jsonl(INCIDENTS)

    # 1) All impacted are contested
    status_map = {s["id"]: s for s in status}
    impacted = [
        d["id"] for d in decisions if "provenance" in d.get("question_attrs", [])
    ]
    # also impacted if any evidence has provenance attribute (conservative)
    # this matches the injection logic in s2_contradiction.py via DEC_STAT
    impacted = sorted(set(impacted + [s["id"] for s in status if s.get("contested")]))

    no_unflagged_impacted = all(
        status_map.get(i, {}).get("contested") for i in impacted
    )

    # 2) Retro rule exists and references provenance
    retro_ok = os.path.exists(RETRO)
    retro_ref_ok = False
    if retro_ok:
        txt = open(RETRO, "r", encoding="utf-8").read()
        retro_ref_ok = ("RR-0001" in txt) and ("provenance" in txt)

    # 3) Retro rule created within 2h of injection (from incidents.ndjson)
    inject_ts = None
    retro_ts = None
    for e in incidents:
        if e.get("type") == "contradiction_injection":
            inject_ts = parse_iso(e["timestamp"])
        if e.get("type") == "retro_rule_created":
            retro_ts = parse_iso(e["timestamp"])
    time_ok = False
    retro_rule_time_hours = None
    if inject_ts and retro_ts:
        delta = retro_ts - inject_ts
        retro_rule_time_hours = delta.total_seconds() / 3600.0
        time_ok = retro_rule_time_hours <= 2.0

    # 4) S1 still passes
    p = subprocess.run(
        [sys.executable, "spec_pack/tools/run_s1.py"], capture_output=True, text=True
    )
    s1_pass = p.returncode == 0

    summary = {
        "H-S2-01": {
            "no_unflagged_impacted": no_unflagged_impacted,
            "retro_rule_exists": retro_ok and retro_ref_ok,
            "retro_rule_time_hours": retro_rule_time_hours,
            "time_within_2h": time_ok,
        },
        "S1_still_PASS": s1_pass,
    }
    ok = no_unflagged_impacted and retro_ok and retro_ref_ok and time_ok and s1_pass
    print(json.dumps({"S2_pass": ok, "summary": summary}, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
