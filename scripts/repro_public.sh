#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Build verifier docker (pinned)"
docker build -t proofengine/verifier:bench -f Dockerfile.verifier .

echo "[2/4] Bench baseline/shadow/active"
python scripts/bench_2cat.py --suite corpus/bench_public/suite.json --mode baseline --runs 3 --out artifacts/bench_public/metrics_baseline.json
python scripts/bench_2cat.py --suite corpus/bench_public/suite.json --mode active --runs 3 --out artifacts/bench_public/metrics_active.json

echo "[3/4] Pack audit + provenance"
mkdir -p artifacts/bench_public
zip -r artifacts/bench_public/audit_pack.zip artifacts/bench_public/*.json || true
python scripts/provenance.py artifacts/bench_public/audit_pack.zip

if [[ -n "${COSIGN_KEY:-}" ]]; then
  cosign sign-blob --yes --key "$COSIGN_KEY" artifacts/bench_public/audit_pack.zip > artifacts/bench_public/audit.sig
fi

echo "[4/4] Verify (if signature present)"
if [[ -f artifacts/bench_public/audit.sig ]]; then
  cosign verify-blob --key .github/security/cosign.pub --signature artifacts/bench_public/audit.sig artifacts/bench_public/audit_pack.zip
fi

echo "Done. See artifacts/bench_public/"
