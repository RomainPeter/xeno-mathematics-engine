# S2++ Benchmark Suite

## Vue d'ensemble

La suite S2++ étend le corpus S2 avec 20+ cas couvrant :
- **API/Governance** : api-default-change, api-param-rename, breaking-without-bump, changelog-missing, deprecation-unhandled, public-endpoint-removed
- **Supply-chain** : typosquat-requests, transitive-cve, unpinned-dep-drift, image-tag-floating, sbom-tamper, provenance-mismatch, submodule-drift
- **Sécurité/Compliance** : secret-committed, egress-attempt, pii-logging, license-violation-agpl, binary-without-source
- **Robustesse** : flaky-timeout, random-seed-missing, perf-budget-p95, nondet-ordering

## Structure

```
corpus/s2pp/
├── suite.json                    # Configuration de la suite
├── api-default-change/           # Cas API governance
├── typosquat-requests/           # Cas supply-chain
├── secret-committed/             # Cas sécurité
└── flaky-timeout/               # Cas robustesse
```

## Utilisation

### Benchmark complet
```bash
make s2pp-bench
```

### Mode shadow (baseline)
```bash
make s2pp-shadow
```

### Mode actif (avec stratégies 2-cat)
```bash
make s2pp-active
```

### Calibration δ v2
```bash
make s2pp-delta-calibrate
```

### Reproduction publique
```bash
make repro-public-s2pp
```

## Métriques

### Gates d'acceptation
- **Corpus** : ≥20 cas totaux (≥12 nouveaux)
- **δ v2** : Pearson ρ ≥ 0.6, Spearman ρ ≥ 0.6, IC95% bas ≥ 0.5
- **Gains 2-cat** : Δ success rate ≥ +10 pts, overhead ≤ 15%
- **Supply-chain** : SBOM/provenance/license/digest vérifiés

### Stratégies 2-cat
- `require_license_allowlist` : Gestion des licences
- `enforce_digest_pin` : Épinglage des dépendances
- `redact_pii` : Redaction des données PII
- `require_changelog` : Obligation de changelog
- `add_benchmark_then_optimize` : Optimisation des performances
- `add_seed_and_rerun` : Reproducibilité des tests

## Résultats

Les résultats sont sauvegardés dans `artifacts/s2pp/` :
- `metrics.csv` : Données pour calibration
- `weights_v2.json` : Poids optimisés
- `delta_report.json` : Rapport de calibration
- `audit_pack.zip` : Pack d'audit signé

## CI/CD

Le pipeline CI exécute automatiquement :
1. `s2pp-shadow` : Mode baseline
2. `s2pp-active` : Mode avec stratégies
3. `expected-fail-s2pp` : Tests d'échec attendu
4. `bench-s2pp` : Benchmark complet + calibration

## Vérification

```bash
# Vérifier les gates
python -c "
import json
with open('artifacts/s2pp/bench/metrics.json') as f:
    metrics = json.load(f)
print('Gates:', metrics['delta']['meets_gates'])
"

# Vérifier la signature
cosign verify-blob --key .github/security/cosign.pub artifacts/s2pp/audit_pack.zip --signature artifacts/s2pp/audit.sig
```
