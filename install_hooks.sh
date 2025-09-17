#!/usr/bin/env bash
# install_hooks.sh — Installe des hooks Git locaux “stricts” (S1 en pre-commit, S1+S2 en pre-push)
# Usage:
#   ./install_hooks.sh           # installe en sauvegardant d’éventuels hooks existants (*.bak.TIMESTAMP)
#   ./install_hooks.sh --force   # écrase sans sauvegarde
set -euo pipefail

FORCE=0
if [[ "${1-}" == "--force" ]]; then FORCE=1; fi

# 1) Vérifs de base
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${ROOT}" || ! -d "${ROOT}/.git" ]]; then
  echo "Erreur: ce répertoire n’est pas un dépôt Git initialisé. Lance d’abord: git init" >&2
  exit 1
fi
cd "${ROOT}"

command -v python >/dev/null || { echo "Erreur: python introuvable dans le PATH." >&2; exit 1; }

need_files=(
  "spec_pack/tools/run_s1.py"
  "spec_pack/tools/ci_local.sh"
)
for f in "${need_files[@]}"; do
  [[ -f "${f}" ]] || { echo "Erreur: fichier requis manquant: ${f}" >&2; exit 1; }
done
chmod +x spec_pack/tools/ci_local.sh || true

HOOKS="${ROOT}/.git/hooks"
mkdir -p "${HOOKS}"

backup_or_overwrite() {
  local target="$1"
  if [[ -f "${target}" && ${FORCE} -eq 0 ]]; then
    mv "${target}" "${target}.bak.$(date +%s)"
  fi
}

# 2) pre-commit = S1 strict
PRE_COMMIT="${HOOKS}/pre-commit"
backup_or_overwrite "${PRE_COMMIT}"
cat > "${PRE_COMMIT}" <<"EOF"
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
echo "[pre-commit] S1…"
python spec_pack/tools/run_s1.py || { echo "PRE-COMMIT BLOQUÉ: S1 a échoué." >&2; exit 1; }
echo "[pre-commit] OK"
EOF
chmod +x "${PRE_COMMIT}"

# 3) pre-push = S1+S2 strict (sandbox via ci_local.sh)
PRE_PUSH="${HOOKS}/pre-push"
backup_or_overwrite "${PRE_PUSH}"
cat > "${PRE_PUSH}" <<"EOF"
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
echo "[pre-push] CI locale stricte: S1+S2"
./spec_pack/tools/ci_local.sh || { echo "PUSH BLOQUÉ: S1/S2 ont échoué." >&2; exit 1; }
echo "[pre-push] OK"
EOF
chmod +x "${PRE_PUSH}"

echo "Hooks installés:"
echo " - ${PRE_COMMIT} (S1 au pre-commit)"
echo " - ${PRE_PUSH} (S1+S2 au pre-push)"
echo "Astuce: relance avec --force pour écraser des hooks existants."
