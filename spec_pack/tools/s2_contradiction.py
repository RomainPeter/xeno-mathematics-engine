#!/usr/bin/env python3
import json, time, os, subprocess, sys
from datetime import datetime, timezone

EVIDENCE = "spec_pack/samples/evidence.jsonl"
DECISIONS = "spec_pack/samples/decisions.jsonl"
JOURNAL  = "spec_pack/samples/journal.ndjson"
INCIDENTS= "spec_pack/samples/incidents.ndjson"
DEC_STAT = "spec_pack/samples/decisions_status.jsonl"
RETRO    = "spec_pack/retro_rules.yaml"
MERKLE   = "spec_pack/tools/merkle_hasher.py"

CONFLICT_ATTR = "provenance"
ANTAGONIST_ATTR = "deny_provenance"
POISON_ID = "EVID-X-POISON"

def load_jsonl(path):
    if not os.path.exists(path): return []
    with open(path,"r",encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

def dump_jsonl(path, items):
    with open(path,"w",encoding="utf-8") as f:
        for o in items:
            f.write(json.dumps(o, separators=((",",":")))+"\n")

def append_ndjson(path, item):
    with open(path,"a",encoding="utf-8") as f:
        f.write(json.dumps(item, separators=((",",":")))+"\n")

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def ensure_dir(p):
    os.makedirs(os.path.dirname(p), exist_ok=True)

def main():
    ensure_dir(EVIDENCE); ensure_dir(JOURNAL); ensure_dir(RETRO); ensure_dir(INCIDENTS); ensure_dir(DEC_STAT)

    # 1) Inject conflicting evidence
    ev = load_jsonl(EVIDENCE)
    if not any(x.get("id")==POISON_ID for x in ev):
        ev.append({
            "id": POISON_ID,
            "type": "document",
            "title": "Conflicting Policy for Provenance",
            "content_hash": "9"*64,
            "created_at": now_iso(),
            "source": {"system":"GRC","location":"policies/conflict","uri":"internal://policies/conflict"},
            "attributes": [CONFLICT_ATTR, ANTAGONIST_ATTR, "conflict_marker"],
            "obligations": ["O-5"],
            "provenance": [],
            "journal_refs": [],
            "confidentiality":"internal",
            "pii_present": False,
            "tags":["conflict","incident"]
        })
        dump_jsonl(EVIDENCE, ev)

    # 2) Mark impacted decisions as contested
    ev_index = {e["id"]: set(e.get("attributes",[])) for e in ev}
    dec = load_jsonl(DECISIONS)
    contested = []
    for d in dec:
        # Impacted if question or any evidence touches the conflicting attribute
        qattrs = set(d.get("question_attrs", []))
        eattrs = set().union(*(ev_index.get(eid,set()) for eid in d.get("evidence_ids", [])))
        impacted = (CONFLICT_ATTR in qattrs) or (CONFLICT_ATTR in eattrs)
        contested.append({
            "id": d["id"],
            "contested": bool(impacted),
            "reason": f"conflict({CONFLICT_ATTR})" if impacted else None
        })
    dump_jsonl(DEC_STAT, contested)

    # 3) Log incident + retro-implication rule
    ensure_dir(INCIDENTS)
    inj = {
        "id": f"INC-{int(time.time())}",
        "timestamp": now_iso(),
        "type": "contradiction_injection",
        "attribute": CONFLICT_ATTR,
        "antagonist": ANTAGONIST_ATTR,
        "evidence_id": POISON_ID
    }
    append_ndjson(INCIDENTS, inj)

    # Create/update retro_rules.yaml
    rule_yaml = f"""
retro_rules:
  - id: RR-0001
    created_at: "{now_iso()}"
    trigger: "attribute_conflict: {CONFLICT_ATTR} vs {ANTAGONIST_ATTR}"
    statement: "If conflicting policy detected on {CONFLICT_ATTR}, quarantine affected evidence and mark dependent decisions as contested; enforce deny-with-proof for requests requiring {CONFLICT_ATTR} until resolution."
    action:
      - quarantine: "{CONFLICT_ATTR}"
      - mark_decisions: "contested"
      - policy: "deny_with_proof"
    verifier: "v_provenance"
"""
    with open(RETRO, "w", encoding="utf-8") as f:
        f.write(rule_yaml)

    retro_evt = {
        "id": f"INC-{int(time.time())}-retro",
        "timestamp": now_iso(),
        "type": "retro_rule_created",
        "rule_id": "RR-0001",
        "covers_attribute": CONFLICT_ATTR
    }
    append_ndjson(INCIDENTS, retro_evt)

    # 4) Append journal entries (Incident + RetroRule)
    jr = load_jsonl(JOURNAL)
    next_num = len(jr)+1
    j_inc = {
        "id": f"JRNL-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{next_num:04d}",
        "timestamp": now_iso(),
        "actor": {"type":"system","id":"IncidentAgent"},
        "action_type": "Incident",
        "input_refs": [],
        "output_refs": [POISON_ID],
        "obligations_checked": ["O-2","O-5"],
        "invariants_checked": ["I-2","I-7"],
        "verifiers_run": ["v_provenance"],
        "result": "fail",
        "notes": f"Injected contradiction on {CONFLICT_ATTR}"
    }
    next_num += 1
    j_rule = {
        "id": f"JRNL-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{next_num:04d}",
        "timestamp": now_iso(),
        "actor": {"type":"system","id":"RetroRuleEngine"},
        "action_type": "RetroRule",
        "input_refs": [POISON_ID],
        "output_refs": ["RR-0001"],
        "obligations_checked": ["O-10"],
        "invariants_checked": [],
        "verifiers_run": [],
        "result": "pass",
        "notes": "Retro-implication rule created; decisions marked contested"
    }
    append_ndjson(JOURNAL, j_inc)
    append_ndjson(JOURNAL, j_rule)

    # 5) Recompute merkle chain on the journal
    if os.path.exists(MERKLE):
        subprocess.run([sys.executable, MERKLE, "--in", JOURNAL, "--out", JOURNAL], check=True)
    else:
        print("WARN: merkle_hasher.py not found; journal not rehashed", file=sys.stderr)

    print(json.dumps({
        "status":"ok",
        "injected_evidence": POISON_ID,
        "contested_marked": sum(1 for c in contested if c["contested"]),
        "decisions_total": len(contested),
        "retro_rule":"RR-0001",
        "files_written":[EVIDENCE, DEC_STAT, INCIDENTS, RETRO, JOURNAL]
    }, indent=2))

if __name__ == "__main__":
    main()
