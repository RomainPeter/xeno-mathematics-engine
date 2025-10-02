#!/usr/bin/env python3
"""
Round-trip validation script for Proof Engine v0.1 schemas.
Validates JSON schemas, canonicalizes, and checks journal hash chain.
"""

import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

BASE = Path(__file__).resolve().parents[1]  # repo root
SPEC_DIR = BASE / "specs" / "v0.1"
EX_DIR = BASE / "examples" / "v0.1"


def load_schema(name):
    """Load a JSON schema from specs/v0.1/"""
    p = SPEC_DIR / f"{name}.schema.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def validator(schema):
    """Create a validator with registry for local $id refs"""
    # Create registry with all schemas
    registry = Registry()
    for sp in SPEC_DIR.glob("*.schema.json"):
        with open(sp, "r", encoding="utf-8") as f:
            s = json.load(f)
            if "$id" in s:
                resource = Resource.from_contents(s, default_specification=DRAFT202012)
                registry = registry.with_resource(s["$id"], resource)

    return Draft202012Validator(schema, registry=registry)


def canonical(o):
    """Canonicalize JSON object for consistent serialization"""
    return json.dumps(o, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(b):
    """Compute SHA256 hex digest"""
    return hashlib.sha256(b).hexdigest()


def validate_dir(prefix, schema_name):
    """Validate all examples in a directory against their schema"""
    sch = load_schema(schema_name)
    v = validator(sch)
    ok = 0
    for p in (EX_DIR / prefix).glob("*.json"):
        obj = json.loads((p).read_text())
        v.validate(obj)
        # round-trip
        ser = canonical(obj)
        obj2 = json.loads(ser.decode("utf-8"))
        v.validate(obj2)
        assert obj == obj2, f"Round-trip mismatch for {p.name}"
        ok += 1
    print(f"{schema_name}: {ok} examples validated and round-tripped.")


def check_journal_chain():
    """Check journal hash chain integrity (sentinel-only in v0.1)"""
    sch = load_schema("journal")
    v = validator(sch)
    for p in (EX_DIR / "journal").glob("*.json"):
        j = json.loads(p.read_text())
        v.validate(j)
        prev = "0" * 64
        for e in j.get("entries", []):
            assert e["prev_entry_hash"] == prev, f"Bad prev hash at {p.name}:{e['id']}"
            # For v0.1 we only check presence, not recompute entry_hash
            prev = e["entry_hash"]
    print("Journal chain sentinel check passed.")


if __name__ == "__main__":
    try:
        validate_dir("journal", "journal")
        validate_dir("x", "x")
        validate_dir("pcap", "pcap")
        validate_dir("plan", "plan")
        validate_dir("failreason", "failreason")
        check_journal_chain()
        print("All validations passed.")
    except Exception as e:
        print("Validation failed:", e)
        sys.exit(1)
