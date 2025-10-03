#!/usr/bin/env python3
import json
import time
from pathlib import Path

# Stubs d'intégration: importez vos modules si dispo
try:
    from orchestrator.handlers.failreason import handle_fail
    from orchestrator.state import Journal, XState
except Exception:
    handle_fail = None

    class Journal:
        def __init__(self, p):
            self.p = Path(p)
            self.p.parent.mkdir(parents=True, exist_ok=True)

        def append(self, entry):
            with open(self.p, "a") as f:
                f.write(json.dumps(entry) + "\n")

    class XState:
        def __init__(self):
            self.K = []
            self.E = []
            self.H = []

        def add_obligation(self, k):
            self.K.append(k)


state = XState()
journal = Journal("out/J.jsonl")
event = {
    "fail_reason": "ConstraintBreach",
    "details": {
        "policy": "policy.retain_sensitive",
        "case": {"data_class": "sensitive", "has_legal_basis": False},
    },
    "ts": int(time.time()),
}
if handle_fail:
    res = handle_fail(event, state=state, journal=journal)
else:
    # Fallback: simule ajout de règle/test
    state.add_obligation({"type": "opa_rule", "name": "require_legal_basis_for_sensitive"})
    journal.append(
        {
            "type": "FailHandled",
            "reason": "ConstraintBreach",
            "added": "require_legal_basis_for_sensitive",
        }
    )
print("Fire-drill completed. K↑ and journal updated.")
