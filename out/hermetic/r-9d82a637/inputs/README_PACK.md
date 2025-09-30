Hermetic, Attestable Audit Pack (PEFC)

Overview
This document explains how to produce a deterministic, attestable Audit Pack with PEFC.

Badges
- CI Hardening: ![CI Hardening](https://github.com/OWNER/REPO/actions/workflows/ci-harden.yml/badge.svg)
- Pack Verify: ![Pack Verify](https://github.com/OWNER/REPO/actions/workflows/pack-verify.yml/badge.svg)

Prerequisites
- Python 3.11+
- requirements.lock installed exactly

Environment for Reproducibility
- TZ=UTC
- PYTHONHASHSEED=<seed>
- SOURCE_DATE_EPOCH=<unix_epoch>

Quickstart (Local, off-network)
1) Install dependencies strictly:
   pip install -r requirements.lock
2) Run smoke test end-to-end:
   bash scripts/ci/smoke_pack.sh

This will:
- Build a deterministic pack with --no-network
- Verify merkle/manifest and sample proof
- Print merkle root and provenance subject
- Sign provenance in dry-run mode (no keys)

Artifacts Layout
- {audit_dir}/{run_id}/
  - manifest.json
  - merkle.json (order, leaves, proofs, root)
  - provenance.json (SLSA-lite/in-toto minimal)
  - verdict.json
  - logs.jsonl, incidents.jsonl
  - pcaps/

Determinism Notes
- Inputs are normalized (LF, trailing newline, mtime=SOURCE_DATE_EPOCH)
- Order of files is lexicographically sorted
- Merkle root is stored in manifest and cross-checked in merkle.json

Provenance
- subject: merkle_root
- materials: requirements.lock sha256 (if present)
- invocation: seed, allow_outside_workspace, env (TZ, PYTHONHASHSEED, SOURCE_DATE_EPOCH)

Troubleshooting
- PermissionError on Windows: ensure file handles are closed; our sinks reopen per write
- Network detected with --no-network: environment must block DNS/egress; remove flag locally
- Drift in CI: set DRIFT_ACCEPTED=true in PR secrets for intentional changes, and update baselines/pack.merkle.json after merge

Expected Outputs (Example)
- merkle_root: stored in {run_dir}/manifest.json
- verify --file <path> should return file_ok=true when the path is present in merkle.json order






