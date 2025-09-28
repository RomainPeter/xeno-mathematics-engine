# CI: Pack smoke-test

## Vue d'ensemble

Le CI Pack smoke-test garantit en continu l'absence de régression dans la construction et la vérification des packs. Il s'exécute automatiquement sur chaque push vers `main`, pull request, et tag `v*`.

## Fonctionnalités

### Vérifications automatiques

- **Construction du pack** : Utilise `pefc pack build` avec logs JSON
- **Vérification des doublons** : Détecte les doublons d'arcnames dans le ZIP
- **Vérification stricte** : Valide manifest.json, SHA256, et Merkle root
- **Extraction du manifest** : Teste la commande `pefc pack manifest`

### Matrices de test

- **Python** : 3.10, 3.11, 3.12
- **OS** : Ubuntu Latest
- **Dépendances** : Installation automatique avec `pip install -e ".[dev]"`

### Artefacts générés

- **ZIP du pack** : Archive complète avec manifest et merkle
- **manifest.json** : Manifest extrait au format T18
- **verify.json** : Rapport de vérification détaillé
- **merkle_root.txt** : Racine Merkle pour référence

## Configuration

### Workflow GitHub Actions

Le workflow est défini dans `.github/workflows/pack-smoke.yml` :

```yaml
name: Pack smoke-test

on:
  push:
    branches: [ main ]
    tags: [ "v*" ]
  pull_request:
    branches: [ main ]

jobs:
  smoke:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [ "3.10", "3.11", "3.12" ]
```

### Pipeline de construction

Le pipeline utilise `config/pipelines/bench_pack.yaml` avec les étapes :

1. **CollectSeeds** : Collecte des métriques benchmark
2. **ComputeMerkle** : Calcul de la racine Merkle
3. **RenderDocs** : Génération de la documentation
4. **PackZip** : Création du ZIP avec manifest T18
5. **SignArtifact** : Signature (désactivée en CI)

### Configuration CI

- **Signature désactivée** : `sign.enabled: false` dans le profil `dev`
- **Logs JSON** : Activés pour l'intégration avec GitHub Actions
- **Mode non-strict** : Permet les échecs de signature en CI

## Utilisation locale

### Test du workflow

```bash
# Test complet du workflow CI
python test_ci_workflow.py

# Test individuel des composants
python -m pefc.cli --config config/pack.yaml --json-logs pack build --pipeline config/pipelines/bench_pack.yaml --no-strict
python scripts/check_zip_duplicates.py dist/dist/*.zip
python -m pefc.cli pack verify --zip dist/dist/*.zip --strict
python -m pefc.cli pack manifest --zip dist/dist/*.zip --print
```

### Vérification des doublons

```bash
# Script de vérification des doublons
python scripts/check_zip_duplicates.py <zip_path>
```

## Critères d'acceptation

### ✅ Le job échoue si

- `pefc pack verify --strict` retourne une erreur
- Des doublons d'arcnames sont détectés dans le ZIP
- Le manifest n'est pas conforme au schéma T18

### ✅ Le job publie systématiquement

- Le ZIP construit
- manifest.json extrait
- verify.json (rapport de vérification)
- merkle_root.txt

### ✅ Le résumé CI contient

- Nom du ZIP et taille
- Racine Merkle
- Nombre de fichiers
- Durée d'exécution
- Rapport de vérification détaillé

## Intégration T18

Le CI utilise le nouveau format de manifest T18 avec :

- **format_version** : "1.0"
- **pack_name, version, built_at** : Métadonnées du pack
- **builder** : {cli_version, host}
- **file_count, total_size_bytes** : Statistiques
- **merkle_root** : Racine Merkle (hex, 64 chars)
- **files** : Liste avec {path, size, sha256, leaf}
- **signature** : {present, provider?, signature_path?} (optionnel)

## Dépannage

### Erreurs communes

1. **Doublons d'arcnames** : Vérifier que `manifest.json` et `merkle.txt` ne sont pas ajoutés deux fois
2. **Manifest invalide** : S'assurer que le format T18 est utilisé
3. **Merkle root mismatch** : Vérifier que `manifest.json` et `merkle.txt` sont exclus du calcul Merkle

### Logs utiles

- **Logs JSON** : Activés avec `--json-logs` pour l'intégration GitHub Actions
- **Rapport de vérification** : Disponible dans `verify.json`
- **Manifest complet** : Extrait avec `pefc pack manifest --print`

## Évolutions futures

- **Tests de performance** : Mesure des temps de construction
- **Tests de compatibilité** : Vérification avec différentes versions Python
- **Tests de sécurité** : Validation des signatures (quand activées)
- **Tests de régression** : Comparaison avec les builds précédents
