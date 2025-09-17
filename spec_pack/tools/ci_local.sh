#!/usr/bin/env bash
set -euo pipefail
echo "[CI local] S1…"
python3 spec_pack/tools/run_s1.py
echo "[CI local] S2 sandbox…"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
rsync -a spec_pack "$TMP"/
pushd "$TMP" >/dev/null
python3 spec_pack/tools/s2_contradiction.py
python3 spec_pack/tools/s2_check.py
popd >/dev/null
echo "[CI local] OK: S1+S2 PASS"
