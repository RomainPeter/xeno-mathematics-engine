#!/usr/bin/env bash
set -euo pipefail
PACK="vendor/2cat/2cat-pack.tar.gz"
SIG="${PACK}.minisig"
LOCK="vendor/2cat/2cat.lock"
[ -f "$PACK" ] && [ -f "$SIG" ] && [ -f "$LOCK" ] || { echo "Missing pack/signature/lock"; exit 2; }
EXPECTED_SHA=$(grep '^sha256:' "$LOCK" | cut -d: -f2)
PUBKEY=$(grep '^pubkey:' "$LOCK" | cut -d: -f2-)
ACTUAL_SHA=$(shasum -a 256 "$PACK" | awk '{print $1}')
[ "$EXPECTED_SHA" = "$ACTUAL_SHA" ] || { echo "SHA256 mismatch"; exit 3; }
minisign -V -P "$PUBKEY" -m "$PACK" -x "$SIG" >/dev/null
echo "2cat pack verified"
