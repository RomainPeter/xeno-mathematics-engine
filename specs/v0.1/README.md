# Proof Engine v0.1 Schemas

This directory contains the JSON schemas for Proof Engine v0.1, defining the core data structures for hybrid proof orchestration.

## Schemas

- **`journal.schema.json`** - Structured Journal (append-only, chained entries)
- **`x.schema.json`** - Cognitive State X (H, E, K, A, J, Σ)
- **`pcap.schema.json`** - Proof-Carrying Action (PCAP)
- **`plan.schema.json`** - Strategic Plan Π
- **`failreason.schema.json`** - FailReason taxonomy

## Examples

Each schema has 3 example files in `../examples/v0.1/`:
- `ex1.json` - Basic example
- `ex2.json` - Complex example with multiple entries/items
- `ex3.json` - Edge case (empty or minimal)

## Validation

Run the round-trip validation script:

```bash
python scripts/test_roundtrip.py
```

This validates:
- JSON Schema compliance
- Round-trip serialization/deserialization
- Journal hash chain integrity (sentinel check)

## Schema Features

### Journal (J)
- Append-only entries with chained hashes
- 7 operators: Meet, Refute, Generalize, Specialize, Contrast, Normalize, Verify
- Cost vector V: time_ms, audit_cost, security_risk, info_loss, tech_debt

### Cognitive State (X)
- H: Hypotheses (open/supported/refuted)
- E: Evidence (doc/code/test/policy/dataset/runlog)
- K: Constraints (internal/eu_ai_act/nist_rmF/iso_42001/semver/custom)
- A: Artifacts (code_change/doc/dataset/model_card/plan/pcap)
- J: Journal reference
- Σ: Seed/Environment (repo, branch, commit, tooling)

### PCAP
- Action with name, params, target
- Context hash for state snapshot
- Obligations array
- Justification (cost vector V)
- Proofs array (unit_test/property_test/policy_check/static_analysis)
- Optional attestation with verdict

### Plan (Π)
- Goal and status (pending/running/completed/failed)
- Steps with operators and input/output refs
- Budgets (time_ms, audit_cost, max_replans)

### FailReason
- 8 error codes: parse_error, test_failure, policy_violation, budget_exceeded, verification_timeout, type_error, missing_obligation, insufficient_coverage
- Message, refs, and optional data object

## Next Steps

1. **CLI Toolchain**: `pcap new|pack|verify|attest` commands
2. **Orchestrator**: Plan-Execute-Replan loop with FailReason handling
3. **Verifier**: Hermetic runner with attestation
4. **Shock Ladder**: S1 corpus with δ/V metrics
