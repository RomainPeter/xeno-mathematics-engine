#!/usr/bin/env python3
import argparse
import json
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple

try:
    import yaml
except ImportError:
    yaml = None


def load_yaml_or_json(path: str) -> Any:
    p = Path(path)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()
    if path.endswith(".json"):
        return json.loads(text)
    if yaml:
        return yaml.safe_load(text)
    # fallback naive JSON if yaml missing and file is json-like
    return json.loads(text)


def find_anf() -> Tuple[str, Any]:
    candidates = [
        "spec_pack/anf.yaml",
        "spec_pack/anf.json",
        "spec_pack/ambition.json",
        "spec_pack/ambition.yaml",
    ]
    for c in candidates:
        data = load_yaml_or_json(c)
        if data:
            return c, data
    raise FileNotFoundError(
        "ANF not found (expected one of anf.yaml/anf.json/ambition.json/ambition.yaml under spec_pack/)"
    )


def canonical_json(o: Any) -> str:
    return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_list_ids(path: str, key: str = "id") -> List[str]:
    p = Path(path)
    if not p.exists():
        return []
    data = load_yaml_or_json(path)
    if isinstance(data, list):
        return [str(x.get(key)).strip() for x in data if isinstance(x, dict) and key in x]
    # tests/*.yaml style
    if isinstance(data, dict) and "tests" in data and isinstance(data["tests"], list):
        return [str(t.get(key)).strip() for t in data["tests"] if isinstance(t, dict) and key in t]
    return []


def load_tests_ids() -> List[str]:
    ids = []
    tdir = Path("spec_pack/tests")
    if not tdir.exists():
        return ids
    for p in sorted(tdir.glob("*.yaml")):
        ids.extend(load_list_ids(str(p)))
    return [i for i in ids if i]


def load_rules() -> List[Dict[str, Any]]:
    data = load_yaml_or_json("spec_pack/a2h_rules.yaml")
    if not data or "rules" not in data:
        raise RuntimeError("Missing spec_pack/a2h_rules.yaml or no rules key")
    return data["rules"]


def anf_clauses(anf: Dict[str, Any]) -> Dict[str, List[str]]:
    a = anf.get("ambition", {})
    out = {
        "guarantee": a.get("guarantees", []) or [],
        "constraint": [],
        "non_negotiable": a.get("non_negotiables", []) or [],
        "threat_actor": a.get("threat_actors", []) or [],
        "scope_standards": a.get("scope", {}).get("standards", []) or [],
        "exclusion": a.get("exclusions", []) or [],
    }
    # constraints may be strings or objects
    for c in a.get("constraints", []) or []:
        if isinstance(c, str):
            out["constraint"].append(c)
        elif isinstance(c, dict):
            # normalize key:value to key=value string
            for k, v in c.items():
                out["constraint"].append(f"{k}={v}")
    # normalize known shortcuts
    # accept "air_gapped_option" or C-5=true forms
    env = a.get("environment", []) or []
    if any(str(x).lower().strip() == "air_gapped_option" for x in env):
        out["constraint"].append("air_gapped_option")
    return out


def expand_required_from_rules(
    clauses: Dict[str, List[str]], rules: List[Dict[str, Any]]
) -> Dict[str, List[str]]:
    req = {"obligations": [], "invariants": [], "tests": [], "operators": []}
    for r in rules:
        cond = r.get("when", {})
        typ = cond.get("type")
        val = cond.get("value")
        val_any = cond.get("value_any_of")
        hits = False
        if typ in clauses:
            if val is not None:
                hits = any(str(x) == str(val) for x in clauses[typ])
            elif val_any:
                hits = any(str(x) in [str(v) for v in val_any] for x in clauses[typ])
        if hits:
            em = r.get("emits", {})
            for k in req.keys():
                req[k].extend([str(x) for x in em.get(k, [])])
    # dedup while preserving order
    for k in req:
        seen = set()
        dedup = []
        for x in req[k]:
            if x and x not in seen:
                seen.add(x)
                dedup.append(x)
        req[k] = dedup
    return req


def build_semantics_and_proof(required, present, anf_src, anf_obj, rules_used):
    from z3 import Solver, Bool, sat

    solver = Solver()
    labels = {}
    bools = {}

    # For each required artifact id X, create Bool X, assert equivalence to presence, and track X must be True
    def add_group(kind: str):
        for _id in required.get(kind, []):
            v = Bool(f"{kind}:{_id}")
            bools[_id] = v
            is_present = _id in present[kind]
            # constraint: v == is_present
            solver.add(v == True if is_present else v == False)
            # tracked assertion that v must be True (if not present, contradiction)
            lbl = Bool(f"need_{kind}:{_id}")
            labels[_id] = lbl
            solver.assert_and_track(v, lbl)

    present_sets = {
        "obligations": set(present.get("obligations", [])),
        "invariants": set(present.get("invariants", [])),
        "tests": set(present.get("tests", [])),
        "operators": set(present.get("operators", [])),  # operators optional in v0.3
    }
    add_group("obligations")
    add_group("invariants")
    add_group("tests")
    # operators are informative; do not force unsat if missing

    # produce result
    res = solver.check()
    sat_ok = res == sat
    core = []
    if not sat_ok:
        # collect unsat core labels (missing required ones)
        for a in solver.unsat_core():
            core.append(str(a))

    # Emit proof json
    compiled_dir = Path("spec_pack/compiled")
    compiled_dir.mkdir(parents=True, exist_ok=True)
    anf_canon = canonical_json(anf_obj)
    proof = {
        "anf_path": anf_src,
        "anf_hash_sha256": sha256_str(anf_canon),
        "rules_file": "spec_pack/a2h_rules.yaml",
        "required": required,
        "present": {k: list(v) if isinstance(v, set) else v for k, v in present_sets.items()},
        "status": "SAT" if sat_ok else "UNSAT",
        "unsat_core": core,
        "rules_used": rules_used,
    }
    with open(compiled_dir / "a2h_proof.json", "w", encoding="utf-8") as f:
        json.dump(proof, f, indent=2, ensure_ascii=False)
    return sat_ok, proof


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="vérifie et renvoie code 1 si UNSAT")
    ap.add_argument("--emit", action="store_true", help="écrit le certificat a2h_proof.json")
    args = ap.parse_args()

    anf_path, anf = find_anf()

    # load rules
    rules = load_rules()

    # extract clauses
    clauses = anf_clauses(anf)

    # compute required from rules
    req = expand_required_from_rules(clauses, rules)

    # present artifacts
    present = {
        "obligations": load_list_ids("spec_pack/obligations.yaml"),
        "invariants": load_list_ids("spec_pack/invariants.yaml"),
        "tests": load_tests_ids(),
        "operators": [],  # not enforced in v0.3
    }

    sat_ok, proof = build_semantics_and_proof(req, present, anf_path, anf, [r["id"] for r in rules])

    if args.emit and not args.check:
        print("A2H semantics proof written to spec_pack/compiled/a2h_proof.json")

    if args.check and not sat_ok:
        # Print concise summary for CI
        missing = [lbl.replace("need_", "") for lbl in proof.get("unsat_core", [])]
        sys.stderr.write("A2H semantics UNSAT — missing artifacts: " + ", ".join(missing) + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
