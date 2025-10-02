#!/usr/bin/env bash
set -euo pipefail

# Configuration
PACK="vendor/2cat/2cat-pack.tar.gz"
SIG="${PACK}.minisig"
LOCK="vendor/2cat/2cat.lock"

# Check if all required files exist
MISSING_FILES=()
[ ! -f "$PACK" ] && MISSING_FILES+=("$PACK")
[ ! -f "$SIG" ] && MISSING_FILES+=("$SIG")
[ ! -f "$LOCK" ] && MISSING_FILES+=("$LOCK")

# Skip verification if files are missing and not forced
if [ ${#MISSING_FILES[@]} -gt 0 ]; then
  if [ "${FORCE_VERIFY_2CAT:-0}" != "1" ]; then
    echo "2cat verification skipped (missing files: ${MISSING_FILES[*]}). Set FORCE_VERIFY_2CAT=1 to enforce."
    exit 0
  else
    echo "Missing files: ${MISSING_FILES[*]} and FORCE_VERIFY_2CAT=1 set. Failing."
    exit 2
  fi
fi

# Parse lock file
EXPECTED_SHA=$(grep '^sha256:' "$LOCK" | cut -d: -f2)
EXPECTED_SIZE=$(grep '^size:' "$LOCK" | cut -d: -f2)
PUBKEY=$(grep '^pubkey:' "$LOCK" | cut -d: -f2-)

# Verify SHA256
ACTUAL_SHA=$(shasum -a 256 "$PACK" | awk '{print $1}')
if [ "$EXPECTED_SHA" != "$ACTUAL_SHA" ]; then
  echo "SHA256 mismatch: expected $EXPECTED_SHA, got $ACTUAL_SHA"
  exit 3
fi

# Verify size
ACTUAL_SIZE=$(stat -c%s "$PACK" 2>/dev/null || stat -f%z "$PACK" 2>/dev/null || echo "0")
if [ "$EXPECTED_SIZE" != "$ACTUAL_SIZE" ]; then
  echo "Size mismatch: expected $EXPECTED_SIZE, got $ACTUAL_SIZE"
  exit 4
fi

# Verify signature
if ! minisign -V -P "$PUBKEY" -m "$PACK" -x "$SIG" >/dev/null 2>&1; then
  echo "Signature verification failed"
  exit 5
fi

echo "2cat pack verified (sha256: $ACTUAL_SHA, size: $ACTUAL_SIZE)"
