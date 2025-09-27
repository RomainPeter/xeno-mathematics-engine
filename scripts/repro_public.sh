#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Build verifier docker (pinned)"
docker build -t proofengine/verifier:bench -f Dockerfile.verifier .

echo "[2/4] Bench baseline/shadow/active"
python scripts/bench_2cat.py --suite corpus/bench_public/suite.json --mode baseline --runs 3 --out artifacts/bench_public/metrics_baseline.json
python scripts/bench_2cat.py --suite corpus/bench_public/suite.json --mode active --runs 3 --out artifacts/bench_public/metrics_active.json

echo "[2.5/4] S2++ benchmark with policy flags"
python scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes baseline,active --runs 3 --out artifacts/s2pp/repro
python scripts/delta_calibrate.py --input artifacts/s2pp/repro/metrics.csv --out configs/weights_v2.json --report artifacts/s2pp/delta_report.json --bootstrap 1000

echo "[2.6/4] Expected-fail tests (PII + License)"
python scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes expected_fail --runs 1 --out artifacts/s2pp/expected_fail

echo "[3/4] Pack audit + provenance"
mkdir -p artifacts/bench_public
mkdir -p artifacts/s2pp
zip -r artifacts/bench_public/audit_pack.zip artifacts/bench_public/*.json || true
zip -r artifacts/s2pp/audit_pack.zip artifacts/s2pp/repro/*.json configs/weights_v2.json || true
python scripts/provenance.py artifacts/bench_public/audit_pack.zip
python scripts/provenance.py artifacts/s2pp/audit_pack.zip

if [[ -n "${COSIGN_KEY:-}" ]]; then
  cosign sign-blob --yes --key "$COSIGN_KEY" artifacts/bench_public/audit_pack.zip > artifacts/bench_public/audit.sig
  cosign sign-blob --yes --key "$COSIGN_KEY" artifacts/s2pp/audit_pack.zip > artifacts/s2pp/audit.sig
fi

echo "[4/4] Verify (if signature present)"
if [[ -f artifacts/bench_public/audit.sig ]]; then
  cosign verify-blob --key .github/security/cosign.pub --signature artifacts/bench_public/audit.sig artifacts/bench_public/audit_pack.zip
fi
if [[ -f artifacts/s2pp/audit.sig ]]; then
  cosign verify-blob --key .github/security/cosign.pub --signature artifacts/s2pp/audit.sig artifacts/s2pp/audit_pack.zip
fi

echo "Done. See artifacts/bench_public/ and artifacts/s2pp/"
