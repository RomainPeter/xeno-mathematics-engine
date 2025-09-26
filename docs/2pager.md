# Hybrid Proof-Orchestrator (stochastic inside, deterministic outside)

## Problem
- High oversight cost for autoformalization-like agents: opaque steps, weak traceability, fragile reproducibility.
- Transactional prompting lacks structure for audit and failure recovery.

## Core idea
- Every step becomes a Proof-Carrying Action (PCAP): pre/post, obligations K, cost vector V, delta δ, attested.
- Hybrid loop: stochastic generators propose; deterministic verifier enforces obligations; metacognitive planner selects path.
- On failure: rollback state, record incident, enrich K (rule), re-plan → try again.

## State and artifacts
- Χ = {H hypotheses, E evidences, K obligations, J journal (PCAP), A artifacts, Σ seed/env}.
- PCAP = {operator, pre/post, obligations, justification V, verdict, toolchain, llm_meta}.
- V = [time_ms, backtracks, audit_cost, tech_debt, risk]; δ ~ distance goal↔result (H/E/K/A/J + AST).

## Minimal guarantees
- Append-only PCAP journal; deterministic verifier; attestation (digest, count, verdicts).
- Reproducible runs (seeds, model id, cache); CI cross-OS.

## Demo (code synthesis toy repo)
- Case designed to fail on round 1 (e.g., missing docstrings, high complexity).
- Round 1: plan → variants → verify fails → incident → K+ rule.
- Round 2: re-plan prioritizes fixes → verify passes → attestation ready.
- Replay offline: uses local LLM cache; verifier never calls LLM.

## Metrics (illustrative)
- replan_count = 1; obligations_fixed ≥ 2 (docstring_ok, complexity_ok).
- delta_mean < 0.5; cache_hit ≥ 80%; audit_pack_time < 4 min.
- reviewer_minutes_est (proxy) ↓ vs. naive baseline.

## Why this helps Gauss-like systems
- Lowers supervision cost via structured, attestable steps.
- Provides an audit surface (PCAP, δ, obligations) without binding to a specific prover.
- Integrates as an orchestration layer; candidates for Lean wrappers later.

## Next step (fit probe)
- If useful, define a 2-week micro-pilot: class of subproblems, 3 metrics, interop surface (logs or wrappers), bar for success.

## Implementation notes
- Verifier is hermetic (no LLM); PCAP chain can be validated and replayed.
- Seeds, model id, toolchain recorded for reproducibility.

## Contact
- Repo: <link> | Audit Pack: <link> | LOGS.md: included
