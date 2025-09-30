#!/usr/bin/env bash
set -euo pipefail

AUDIT_DIR="${AUDIT_DIR:-_audit_ci}"
SEED="${SEED:-123}"
# Temps max côté orchestrateur (secondes)
TIME_BUDGET="${TIME_BUDGET:-60}"
# Itérations max côté orchestrateur
MAX_ITERS="${MAX_ITERS:-1}"
KPI_THRESHOLD="${KPI_THRESHOLD:-0.6}"
# Timeout mur global (ex: 8m). GNU timeout sur runners Linux.
DEMO_TIMEOUT="${DEMO_TIMEOUT:-8m}"

echo "[demo] Running lab orchestrator (timeout: ${DEMO_TIMEOUT})..."
timeout "${DEMO_TIMEOUT}" python -u -m orchestrator.cli_lab \
  --lab \
  --seed "${SEED}" \
  --time-budget "${TIME_BUDGET}" \
  --max-iters "${MAX_ITERS}" \
  --hermetic \
  --audit-dir "${AUDIT_DIR}"

status=$?
if [ $status -ne 0 ]; then
  echo "[demo] Orchestrator failed or timed out (exit $status)" >&2
  exit $status
fi

RUN_DIR=$(ls -td "${AUDIT_DIR}"/*/ 2>/dev/null | head -1)
echo "[demo] Latest run dir: ${RUN_DIR:-<none>}"
if [ -z "${RUN_DIR:-}" ]; then
  echo "[demo] No run directory found under ${AUDIT_DIR}" >&2
  exit 1
fi

echo "[demo] Building manifest..."
python scripts/build_manifest.py --audit-dir "${RUN_DIR}"

echo "[demo] Checking KPIs and incidents..."
python scripts/check_e2e.py --run-dir "${RUN_DIR}" --kpi-threshold "${KPI_THRESHOLD}" --require-no-fatal

echo "[demo] Done. Artifacts in: ${RUN_DIR}"


