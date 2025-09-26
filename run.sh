#!/usr/bin/env bash
set -euo pipefail
cmd="${1:-verify}"
case "$cmd" in
  verify) python scripts/verify.py;;
  demo) python scripts/demo.py;;
  audit-pack) python scripts/audit_pack.py;;
  logs) python scripts/make_logs.py;;
  release) python scripts/make_release.py;;
  *) echo "usage: run.sh [verify|demo|audit-pack|logs|release]"; exit 1;;
esac
