# Justification des politiques PR F

## Vue d'ensemble

Ce document justifie les décisions de politique prises pour PR F, avec focus sur la reproductibilité, l'auditabilité et la minimisation des faux positifs.

## 1. Calibration δ v2 : Grid + Bootstrap vs Scikit-learn

### Décision : Grid + Bootstrap (Option A)

**Justification :**
- **Reproductibilité** : Déterministe, pas de dépendances lourdes
- **Auditabilité** : Poids figés + IC95% facilement journalisables
- **Robustesse** : Fonctionne bien sur petit N (≈20-40 cas)
- **Transparence** : Algorithme simple, facile à expliquer

**Contraintes appliquées :**
- Poids ≥ 0 (pas de poids négatifs)
- Somme = 1 (normalisation)
- Résolution grille : 0.05 (équilibre précision/performance)

**Fallback futur :**
- Si corr < 0.6 ou N > 50 cas → basculer sur scikit-learn
- Seuil configurable : `sklearn_threshold: 50`

## 2. PII Detection : Scope et Précision

### Décision : Haute précision, faible bruit

**Patterns activés :**
- **Email** : `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
- **Phone E.164** : `\+?[1-9]\d{7,14}`
- **SSN US** : `\b\d{3}-\d{2}-\d{4}\b`

**Patterns désactivés par défaut :**
- **NIR FR** : `\b\d{13}\b` (flag `pii.fr_nir=false`)
- **Tests fixtures** : Exclusion automatique des dossiers `test/`, `fixture/`, `example/`, `demo/`

**Réduction des faux positifs :**
- Scan uniquement sur diff des sources
- Exclusion des valeurs de test communes (`123-45-6789`, `000-00-0000`)
- Allowlist locale via `.proofignore`

**Redaction automatique :**
- Logs : masquage automatique avant archivage
- Politique OPA : bloque seulement si PII dans code/diff

## 3. Politique Licences : Allowlist vs Denylist

### Décision : Allowlist permissive + Denylist stricte

**Allowlist (licences permissives) :**
- MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, MPL-2.0, ISC
- GPL-2.0-with-classpath-exception (exception contrôlée)

**Denylist (licences incompatibles) :**
- AGPL-3.0, AGPL-3.0-only, AGPL-3.0-or-later
- GPL-3.0, GPL-3.0-only, GPL-3.0-or-later
- SSPL-1.0

**Cas particuliers :**
- **Dual licensing** : OK si une licence est dans l'allowlist
- **UNKNOWN/NOASSERTION** : Warning par défaut (flag `license.unknown=warn`)
- **Exception contrôlée** : Fichier `LICENSE_EXCEPTION.whitelist` avec justification

## Exemples de faux positifs et solutions

### PII Detection

**Faux positif : Email dans test**
```python
# tests/test_email.py
test_email = "user@example.com"  # Ne devrait pas déclencher
```
**Solution :** Exclusion automatique des dossiers `test/`

**Faux positif : NIR dans documentation**
```markdown
# docs/identity.md
NIR example: 1234567890123  # Ne devrait pas déclencher
```
**Solution :** Flag `pii.fr_nir=false` par défaut

### License Detection

**Faux positif : GPL avec exception**
```json
{
  "license": "GPL-2.0-with-classpath-exception"
}
```
**Solution :** Exception explicitement dans l'allowlist

**Faux positif : UNKNOWN dans SBOM**
```json
{
  "licenseConcluded": "UNKNOWN"
}
```
**Solution :** Warning seulement (flag `license.unknown=warn`)

## Configuration des flags

```yaml
# configs/policy_flags.yaml
pii:
  fr_nir: false          # NIR français désactivé
  email: true           # Email activé
  phone_e164: true       # Phone E.164 activé
  ssn_us: true          # SSN US activé

license:
  unknown: "warn"       # UNKNOWN = warning
  dual_license_allow: true  # Dual licensing autorisé
```

## Métriques de qualité

### PII Detection
- **Précision cible** : > 95% (minimiser faux positifs)
- **Rappel cible** : > 90% (détecter vrais PII)
- **Bruit acceptable** : < 5% faux positifs

### License Detection
- **Blocage AGPL/GPLv3** : 100% (zéro tolérance)
- **Warning UNKNOWN** : 100% (tous les cas)
- **Exception contrôlée** : Justification requise

### Calibration δ v2
- **Corrélation cible** : ρ ≥ 0.6
- **IC95% bas** : ≥ 0.5
- **Reproductibilité** : Même résultat sur même dataset

## Évolution future

### v0.2 (si nécessaire)
- **Calibration** : Basculer sur scikit-learn si N > 50 cas
- **PII** : Activer NIR FR si demande explicite
- **Licences** : Rendre UNKNOWN blocant si trop de cas

### v0.3+
- **PII** : Patterns supplémentaires (IBAN, carte bancaire)
- **Licences** : Support licences duales complexes
- **Calibration** : Machine learning avancé

## Validation des gates

### Tests de régression
```bash
# PII : Vérifier exclusion des tests
python scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes expected_fail --filter pii-logging

# Licences : Vérifier blocage AGPL
python scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes expected_fail --filter license-violation-agpl

# Calibration : Vérifier corrélations
python scripts/delta_calibrate.py --input artifacts/s2pp/bench/metrics.csv --out configs/weights_v2.json --report artifacts/s2pp/delta_report.json
```

### Métriques de succès
- **PII** : 0 faux positifs sur tests/fixtures
- **Licences** : 100% blocage AGPL, 0 faux positifs GPL-2.0-with-classpath
- **Calibration** : ρ ≥ 0.6, IC95% ≥ 0.5
