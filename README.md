# Proof Orchestrator – Fit Probe

## Short
Hybrid proof‑carrying orchestration: stochastic generation inside, deterministic verification outside. Every step is a PCAP (typed journal, obligations K, cost vector V, delta δ), with a deterministic verifier and replayable audit pack.

## Scope
- **Today**: code demo (replayable, offline via cache).
- **Tomorrow**: portability to formal mathematics (Gauss‑like pipelines). This is a fit probe, not a Lean integration.

## Why
- Lower oversight cost; raise auditability and reproducibility by construction.
- Structure failures into "incident → rule → non‑regression" loops.

## Quickstart
1) `python3 -m venv .venv && source .venv/bin/activate`
2) `pip install -r requirements.txt`
3) `cp .env.example .env`  # add OPENROUTER_API_KEY and OPENROUTER_MODEL (e.g., x-ai/grok-4-fast:free)
4) `make verify`
5) `make demo`
6) `make audit-pack`
7) `make logs`
8) `make release`

## Verification in 2 minutes
- `make verify`        # LLM ping + JSON strict
- `make demo`          # Plan → Variants → (fail → incident → replan) → success
- `make audit-pack`    # out/audit/attestation.json (digest, count, verdicts)
- `make logs`          # LOGS.md (timeline, obligations snapshot, delta_mean if available)
- `make release`       # dist/audit_pack_<tag>.zip

## Artifacts
- `out/pcap/*.json` (chained Proof‑Carrying Actions)
- `out/audit/attestation.json` (SHA256 digest, verdicts)
- `LOGS.md` (annotated timeline)
- `docs/2pager.md` (architecture and metrics)
- `dist/audit_pack_<tag>.zip` (one‑file bundle)

## Alignment with Math Inc vision
- Expansion (stochastic exploration) + Compression (deterministic verification) per step.
- Network value via reuse/connectivity; audit surface for large‑scale autoformalization.
- Portable orchestration layer; no Lean dependency in this probe.

## Limitations
- Demo in code space only; no claim about Lean/tactics performance.
- LLM ping requires OpenRouter API key; replay uses local cache.

**License**: Apache-2.0