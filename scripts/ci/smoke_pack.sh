#!/usr/bin/env bash
set -euo pipefail

# Smoke test: build → verify → merkle → sign (mock) with --no-network
# Requirements: Python, repo checked out, requirements.lock installed

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"

export TZ=UTC
export PYTHONHASHSEED=${PYTHONHASHSEED:-42}
export SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH:-1700000000}

AUDIT_DIR=${AUDIT_DIR:-out_smoke}
SEED=${SEED:-42}

CONFIG=${CONFIG:-scripts/pack_inputs.example.json}
mkdir -p "$AUDIT_DIR"

echo "[1/4] Build pack (no-network)"
python -m pefc.pack.cli build \
  --config "$CONFIG" \
  --audit-dir "$AUDIT_DIR" \
  --seed "$SEED" \
  --no-network

RUN_DIR=$(ls -td "$AUDIT_DIR"/r-* | head -n1)
echo "RUN_DIR=$RUN_DIR"

echo "[2/4] Verify manifest/merkle and a sample proof (if any file present)"
python -m pefc.pack.cli verify --run-dir "$RUN_DIR"

if [ -f "$RUN_DIR/merkle.json" ]; then
  FILE=$(python - <<'PY'
import json, sys
from pathlib import Path
rd = Path(sys.argv[1])
merkle = json.loads((rd/'merkle.json').read_text())
order = merkle.get('order', [])
print(order[0] if order else '')
PY
"$RUN_DIR")
  if [ -n "$FILE" ]; then
    python -m pefc.pack.cli verify --run-dir "$RUN_DIR" --file "$FILE"
  fi
fi

echo "[3/4] Print merkle root and provenance link"
python - <<'PY'
import json, sys
from pathlib import Path
rd = Path(sys.argv[1])
m = json.loads((rd/'manifest.json').read_text())
prov = json.loads((rd/'provenance.json').read_text())
print('MERKLE_ROOT', m.get('merkle_root'))
print('PROVENANCE_SUBJECT', prov.get('subject'))
PY
"$RUN_DIR"

echo "[4/4] Sign provenance (dry-run)"
python - <<'PY'
from pathlib import Path
from pefc.pack.signing import sign_with_cosign
import sys
rd = Path(sys.argv[1])
sig = sign_with_cosign(rd/'provenance.json', dry_run=True)
print('SIG', sig)
PY
"$RUN_DIR"

echo "[OK] Smoke pack test completed."
