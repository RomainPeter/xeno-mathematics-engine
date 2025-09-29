#!/usr/bin/env bash
set -euo pipefail

AUDIT_DIR="${AUDIT_DIR:-_audit_ci}"
SEED="${SEED:-123}"
TIME_BUDGET="${TIME_BUDGET:-5}"
MAX_ITERS="${MAX_ITERS:-2}"
KPI_THRESHOLD="${KPI_THRESHOLD:-0.6}"

echo "[demo] Running lab orchestrator..."
python -m orchestrator.cli_lab \
  --lab \
  --seed "${SEED}" \
  --time-budget "${TIME_BUDGET}" \
  --max-iters "${MAX_ITERS}" \
  --hermetic \
  --audit-dir "${AUDIT_DIR}"

RUN_DIR=$(ls -td "${AUDIT_DIR}"/*/ | head -1)
echo "[demo] Latest run dir: ${RUN_DIR}"

echo "[demo] Building manifest..."
python scripts/build_manifest.py --audit-dir "${RUN_DIR}"

echo "[demo] Checking KPIs and incidents..."
python scripts/check_e2e.py --run-dir "${RUN_DIR}" --kpi-threshold "${KPI_THRESHOLD}" --require-no-fatal

echo "[demo] Done. Artifacts in: ${RUN_DIR}"


