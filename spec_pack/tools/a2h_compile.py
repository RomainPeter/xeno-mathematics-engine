#!/usr/bin/env python
# A2H: compile ambition.json -> derived mappings + hostility report
import hashlib
import json
import os
import re
import sys
import time

ROOT = "spec_pack"
MANIFEST = f"{ROOT}/ambition/ambition.json"
OUT_DIR = f"{ROOT}/compiled"
OBL_FILE = f"{OUT_DIR}/obligations.auto.json"
INV_FILE = f"{OUT_DIR}/invariants.auto.json"
SHOCK_FILE = f"{OUT_DIR}/shock_ladder.auto.json"
TRACE_FILE = f"{OUT_DIR}/a2h_trace.json"
REPORT = f"{OUT_DIR}/hostility_report.md"
JRNL = f"{ROOT}/samples/journal.ndjson"
OBL_YAML = f"{ROOT}/obligations.yaml"
INV_YAML = f"{ROOT}/invariants.yaml"
TEST_S1 = f"{ROOT}/tests/S1_audit.yaml"
TEST_S2 = f"{ROOT}/tests/S2_incident.yaml"
TEST_S3 = f"{ROOT}/tests/S3_adversarial.yaml"


def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(JRNL), exist_ok=True)


def ids_from_yaml(path, prefix):
    if not os.path.exists(path):
        return set()
    ids = set()
    pat = re.compile(rf"\b{prefix}-[A-Z0-9-]+\b")
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            ids.update(pat.findall(line))
    return ids


def derive(anf):
    edges = []

    def edge(src, dst, why):
        edges.append({"from": src, "to": dst, "rule": why})

    # Required core (doivent exister aujourd'hui)
    req_obl = set()
    req_inv = set()
    req_tests = {"S1": ["H-S1-01"], "S2": ["H-S2-01"]}
    opt_obl = set()
    opt_inv = set()
    opt_tests = {"S1": [], "S2": [], "S3": []}

    # Guarantees → requirements
    for g in anf.get("guarantees", []):
        gid = g.get("id")
        if gid == "G-1":  # minimalité
            req_obl.add("O-1")
            req_inv.add("I-6")
            edge("G-1", "O-1", "minimality→obligation")
            edge("G-1", "I-6", "minimality→invariant")
        if gid == "G-2":  # journal/explicabilité
            req_obl.add("O-2")
            req_inv.add("I-7")
            edge("G-2", "O-2", "journal→obligation")
            edge("G-2", "I-7", "journal→invariant")
        if gid == "G-3":  # audit 24h (optionnel v0.2)
            opt_obl.add("O-3")
            edge("G-3", "O-3", "audit24h→obligation")
        if gid == "G-4":  # borne K
            req_obl.add("O-4")
            req_inv.add("I-5")
            edge("G-4", "O-4", "trace_bound→obligation")
            edge("G-4", "I-5", "trace_bound→invariant")
        if gid == "G-5":  # monotonie
            req_inv.add("I-1")
            edge("G-5", "I-1", "monotonicity→invariant")

    # Constraints / Non-négociables / Menaces
    for c in anf.get("constraints", []):
        cid = c.get("id")
        if cid == "C-3":
            req_obl.add("O-5")
            req_inv.add("I-2")
            edge("C-3", "O-5", "provenance→obligation")
            edge("C-3", "I-2", "provenance→invariant")
        if cid == "C-4":
            opt_obl.add("O-6")
            req_inv.add("I-3")
            edge("C-4", "O-6", "determinism→obligation")
            edge("C-4", "I-3", "determinism→invariant")
        if cid == "C-5":
            opt_obl.add("O-7")
            edge("C-5", "O-7", "air_gapped→obligation")
    for nn in anf.get("non_negociables", []):
        nid = nn.get("id")
        if nid == "NN-2":
            req_inv.add("I-4")
            edge("NN-2", "I-4", "reversibility→invariant")
        if nid == "NN-3":
            opt_obl.add("O-12")
            edge("NN-3", "O-12", "no_blackbox→obligation")
    for ta in anf.get("threat_actors", []):
        tid = ta.get("id")
        if tid == "TA-1":
            opt_obl.add("O-8")
            edge("TA-1", "O-8", "malicious_auditor→deny_with_proof")
        if tid == "TA-2":
            opt_obl.add("O-10")
            edge("TA-2", "O-10", "data_poisoner→retro_implication")

    compiled = {
        "required": {
            "obligations": sorted(req_obl),
            "invariants": sorted(req_inv),
            "tests": req_tests,
        },
        "optional": {
            "obligations": sorted(opt_obl),
            "invariants": sorted(opt_inv),
            "tests": opt_tests,
        },
        "edges": edges,
    }
    return compiled


def write_json(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def append_journal(manifest_hash, compiled_hash):
    entry = {
        "id": "JRNL-" + time.strftime("%Y%m%d") + "-A2H",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "actor": {"type": "system", "id": "A2HCompiler"},
        "action_type": "Compile",
        "input_refs": [f"ANF:{manifest_hash}"],
        "output_refs": [f"compiled:{compiled_hash}"],
        "obligations_checked": ["O-2"],
        "invariants_checked": [],
        "verifiers_run": [],
        "result": "pass",
        "notes": "Ambition compiled to obligations/invariants/tests (required/optional)",
    }
    rows = []
    if os.path.exists(JRNL):
        with open(JRNL, "r", encoding="utf-8") as f:
            rows = [json.loads(l) for l in f if l.strip()]
    rows.append(entry)
    with open(JRNL, "w", encoding="utf-8") as f:
        for o in rows:
            f.write(json.dumps(o, separators=(",", ":")) + "\n")


def sha256_bytes(b):
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def main():
    mode = "emit"
    if len(sys.argv) > 1 and sys.argv[1] in ["--check", "--emit"]:
        mode = "check" if sys.argv[1] == "--check" else "emit"

    anf = load_json(MANIFEST)
    ensure_dirs()
    compiled = derive(anf)

    # Lire les artefacts manuels actuels
    obl_ids = ids_from_yaml(OBL_YAML, "O")
    inv_ids = ids_from_yaml(INV_YAML, "I")
    s1_ids = ids_from_yaml(TEST_S1, "H")
    s2_ids = ids_from_yaml(TEST_S2, "H")
    ids_from_yaml(TEST_S3, "H")

    # Écarts (required)
    miss_obl = sorted(list(set(compiled["required"]["obligations"]) - obl_ids))
    miss_inv = sorted(list(set(compiled["required"]["invariants"]) - inv_ids))
    tests_ok = {
        "S1": all(i in s1_ids for i in compiled["required"]["tests"]["S1"]),
        "S2": all(i in s2_ids for i in compiled["required"]["tests"]["S2"]),
        "S3": True,  # rien d'obligatoire en S3 au v0.2
    }

    # Persister les auto-artefacts
    write_json(
        OBL_FILE,
        compiled["required"] | {"optional_obligations": compiled["optional"]["obligations"]},
    )
    write_json(
        INV_FILE,
        {
            "required": compiled["required"]["invariants"],
            "optional": compiled["optional"]["invariants"],
        },
    )
    write_json(
        SHOCK_FILE,
        {
            "required": compiled["required"]["tests"],
            "optional": compiled["optional"]["tests"],
        },
    )
    write_json(TRACE_FILE, {"edges": compiled["edges"]})

    # Rapport
    rep = f"""# Hostility Report (A2H)
Ambition: {anf.get("title")} (id {anf.get("id")}, v{anf.get("version")})
Mission: {anf.get("mission")}

Required:
- Obligations: {compiled["required"]["obligations"]} → missing vs manual: {miss_obl or "none"}
- Invariants:  {compiled["required"]["invariants"]} → missing vs manual: {miss_inv or "none"}
- Tests:       S1={tests_ok["S1"]} (need {compiled["required"]["tests"]["S1"]}), S2={tests_ok["S2"]} (need {compiled["required"]["tests"]["S2"]})

Optional (not required to pass):
- Obligations: {compiled["optional"]["obligations"]}
- Invariants:  {compiled["optional"]["invariants"]}
- Tests:       {compiled["optional"]["tests"]}

Edges (sample):
"""
    for e in compiled["edges"][:10]:
        rep += f"- {e['from']} → {e['to']} ({e['rule']})\n"
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(rep)

    # Journal
    man_hash = sha256_bytes(json.dumps(anf, separators=(",", ":")).encode())
    comp_hash = sha256_bytes(json.dumps(compiled, separators=(",", ":")).encode())

    if mode == "emit":
        append_journal(man_hash, comp_hash)
        print(
            json.dumps(
                {
                    "status": "emitted",
                    "report": REPORT,
                    "missing_required_obligations": miss_obl,
                    "missing_required_invariants": miss_inv,
                    "tests_required_ok": tests_ok,
                },
                indent=2,
            )
        )
        return 0
    else:
        ok = (not miss_obl) and (not miss_inv) and all(tests_ok.values())
        print(
            json.dumps(
                {
                    "A2H_check_ok": ok,
                    "missing_obligations": miss_obl,
                    "missing_invariants": miss_inv,
                    "tests_required_ok": tests_ok,
                },
                indent=2,
            )
        )
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
