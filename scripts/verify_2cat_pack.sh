#!/usr/bin/env bash
set -euo pipefail
PACK="vendor/2cat/2cat-pack.tar.gz"
SIG="${PACK}.minisig"
LOCK="vendor/2cat/2cat.lock"

# Skip verification by default if files are missing and not forced
if [ ! -f "$PACK" ] || [ ! -f "$SIG" ] || [ ! -f "$LOCK" ]; then
  if [ "${FORCE_VERIFY_2CAT:-0}" != "1" ]; then
    echo "2cat verification skipped (missing files). Set FORCE_VERIFY_2CAT=1 to enforce."
    exit 0
  else
    echo "Missing pack/signature/lock and FORCE_VERIFY_2CAT=1 set. Failing."
    exit 2
  fi
fi
EXPECTED_SHA=$(grep '^sha256:' "$LOCK" | cut -d: -f2)
PUBKEY=$(grep '^pubkey:' "$LOCK" | cut -d: -f2-)
ACTUAL_SHA=$(shasum -a 256 "$PACK" | awk '{print $1}')
[ "$EXPECTED_SHA" = "$ACTUAL_SHA" ] || { echo "SHA256 mismatch"; exit 3; }
minisign -V -P "$PUBKEY" -m "$PACK" -x "$SIG" >/dev/null
echo "2cat pack verified"
