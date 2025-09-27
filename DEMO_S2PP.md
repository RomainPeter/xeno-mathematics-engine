# Demo S2++ - Script 10 minutes

## Prérequis
```bash
# Installation
make setup
source .venv/bin/activate

# Vérification des dépendances
pip install -r requirements.txt
pip install -r spec_pack/requirements.txt
```

## Demo rapide (10 minutes)

### 1. Corpus S2++ (2 min)
```bash
# Explorer la structure
ls -la corpus/s2pp/
cat corpus/s2pp/suite.json

# Voir un cas d'exemple
cat corpus/s2pp/api-default-change/case.json
```

### 2. Stratégies 2-cat (3 min)
```bash
# Lister les stratégies
ls proofengine/strategies/require_*.py

# Voir une stratégie
cat proofengine/strategies/require_license_allowlist.py
```

### 3. Benchmark S2++ (3 min)
```bash
# Mode shadow (baseline)
make s2pp-shadow

# Mode actif (avec stratégies)
make s2pp-active

# Voir les résultats
ls -la artifacts/s2pp/
```

### 4. Calibration δ v2 (2 min)
```bash
# Benchmark complet
make s2pp-bench

# Calibration des poids
make s2pp-delta-calibrate

# Voir les poids optimisés
cat configs/weights_v2.json
```

## Résultats attendus

### Métriques de succès
- **Delta success rate** : ≥ +10 points
- **Overhead** : ≤ 15%
- **Replans médian** : ≤ 2
- **Cycles** : 0

### Corrélations δ v2
- **Pearson** : ≥ 0.6
- **Spearman** : ≥ 0.6
- **IC95% bas** : ≥ 0.5
- **Audit time** : ≥ 0.5

### Vérification
```bash
# Vérifier les gates
python -c "
import json
with open('artifacts/s2pp/bench/metrics.json') as f:
    metrics = json.load(f)
print('Gates S2++:', metrics['delta']['meets_gates'])
"

# Vérifier la calibration
python -c "
import json
with open('artifacts/s2pp/delta_report.json') as f:
    report = json.load(f)
print('Calibration δ v2:', report['calibration_results'])
"
```

## Reproduction publique

```bash
# Reproduction complète
make repro-public-s2pp

# Vérifier la signature
cosign verify-blob --key .github/security/cosign.pub artifacts/s2pp/audit_pack.zip --signature artifacts/s2pp/audit.sig
```

## Cas d'usage

### API Governance
```bash
# Cas : api-default-change
python scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes baseline,active --runs 1 --out artifacts/s2pp/demo
```

### Supply-chain
```bash
# Cas : typosquat-requests
python scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes baseline,active --runs 1 --out artifacts/s2pp/demo
```

### Sécurité
```bash
# Cas : secret-committed
python scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes baseline,active --runs 1 --out artifacts/s2pp/demo
```

## Troubleshooting

### Erreurs communes
1. **Module not found** : Vérifier l'activation du venv
2. **Permission denied** : Vérifier les permissions sur artifacts/
3. **Cosign error** : Vérifier la présence des clés

### Debug
```bash
# Logs détaillés
export DEBUG=1
make s2pp-bench

# Vérification des fichiers
ls -la artifacts/s2pp/
cat artifacts/s2pp/bench/metrics.json
```
