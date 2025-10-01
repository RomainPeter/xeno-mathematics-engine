Merci de votre contribution à XME.

Processus court:
- Créez une branche `chore/`, `feat/` ou `fix/`
- Ajoutez des tests
- Assurez `pre-commit run -a` vert
- Ouvrez une PR avec description et critères de validation

Outils standard:
- Nix + direnv (devshell)
- Ruff/Black/Mypy
- Pytest

- Use Conventional Commits (feat:, fix:, docs:, chore:).
- Before pushing: run make a2h && make s1 && make s2 (or rely on hooks).
- Open PRs to main; Proof CI must pass (A2H+S1+S2).

## Pré-commit (lint/type/sécurité)

Installer les hooks localement pour accélérer les retours et éviter les échecs CI:

```bash
pip install pre-commit
pre-commit install
# Optionnel: exécuter sur tout le repo
pre-commit run --all-files
```

Hooks configurés dans `.pre-commit-config.yaml`:
- ruff (lint/format, avec --fix)
- mypy (typage) sur `pefc`, `orchestrator`, `scripts`
- bandit (sécurité) sur `pefc`

Conseil: si vous mettez à jour des dépendances, assurez-vous d’utiliser `requirements.lock` et de vérifier `pip-audit`.