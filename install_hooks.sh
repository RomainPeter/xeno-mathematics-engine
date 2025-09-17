#!/usr/bin/env bash
set -euo pipefail
FORCE=0
if [[ "${1:-}" == "--force" ]]; then FORCE=1; fi
mkdir -p .git/hooks

install_hook () {
  local name="$1" ; local body="$2"
  local path=".git/hooks/$name"
  if [[ -f "$path" && $FORCE -eq 0 ]]; then
    echo "[install_hooks] $name existe déjà. Utilise --force pour écraser."
    return 0
  fi
  printf "%s\n" "$body" > "$path"
  chmod +x "$path"
  echo "[install_hooks] $name installé."
}

PRE_COMMIT='#!/usr/bin/env bash
set -euo pipefail
# 1) Ambition->Hostility doit être cohérent
python spec_pack/tools/a2h_compile.py --check
# 2) S1 doit passer
python spec_pack/tools/run_s1.py
echo "[pre-commit] OK (A2H+S1)"'

PRE_PUSH='#!/usr/bin/env bash
set -euo pipefail
echo "[pre-push] A2H_check + CI locale (S1+S2)"
python spec_pack/tools/a2h_compile.py --check
./spec_pack/tools/ci_local.sh
echo "[pre-push] OK (A2H+S1+S2)"'

install_hook "pre-commit" "$PRE_COMMIT"
install_hook "pre-push" "$PRE_PUSH"
echo "[install_hooks] Terminé. Utilise --force pour réinstaller."