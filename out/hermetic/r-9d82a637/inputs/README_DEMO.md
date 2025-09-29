# Orchestrator (Lab-Grade) — E2E Demo

This repository provides a hermetic AE → CEGIS orchestration demo with structured telemetry, KPIs, and auditable artifacts.

Badges
- Orchestrator E2E: ![Orchestrator E2E](https://github.com/OWNER/REPO/actions/workflows/orchestrator-e2e.yml/badge.svg)
- CI Hardening: ![CI Hardening](https://github.com/OWNER/REPO/actions/workflows/ci-harden.yml/badge.svg)

## Quick start

```bash
# Optional env vars
export AUDIT_DIR=_audit_ci
export SEED=123
export TIME_BUDGET=5
export MAX_ITERS=2
export KPI_THRESHOLD=0.6

bash scripts/demo_orchestrator.sh
```

The demo will:
- launch `orchestrator.cli_lab` (OrchestratorLite — hermetic),
- write `journal.jsonl` and `metrics.json` under `${AUDIT_DIR}/{run_id}/`,
- build `manifest.json` (Merkle sum over artifacts),
- validate KPIs/incidents via `scripts/check_e2e.py` (fails if KPI below threshold, fatal incidents present, or missing artifacts).

## Artifacts
- `journal.jsonl` — structured telemetry (JSON Lines)
- `metrics.json` — lab-grade KPIs (AE/CEGIS/Global)
- `manifest.json` — inventory + Merkle root

## CI
The workflow `.github/workflows/orchestrator-e2e.yml`:
- runs the demo with fixed seeds/budgets (no network required),
- uploads artifacts,
- fails if any of:
  - `patch_accept_rate` below the configured threshold,
  - fatal incidents are present,
  - `manifest.merkle_root` is empty.

## Troubleshooting
- Increase `TIME_BUDGET` if you see timeouts.
- Lower `KPI_THRESHOLD` if you need to tolerate lower acceptance in lab.
- Inspect `journal.jsonl` to understand the event sequence.
- Rebuild `manifest.json` if needed:
  ```bash
  python scripts/build_manifest.py --audit-dir "${AUDIT_DIR}/{run_id}"
  ```
