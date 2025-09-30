# Politique de Dérive (Drift)

## Objet
Assurer que toute modification des artefacts déterministes (manifest, merkle, logs, provenance) est intentionnelle et auditée.

## Baseline
- Fichier: `baselines/pack.merkle.json`
- Contient la racine Merkle de référence.

## CI
- Workflow: `.github/workflows/pack-verify.yml`
- Échoue si la racine Merkle courante diffère de la baseline.

## Dérive intentionnelle
1. Ouvrir une PR avec les changements.
2. Définir la variable/secret `DRIFT_ACCEPTED=true` pour lever la barrière sur la PR.
3. Après merge sur `main`, mettre à jour `baselines/pack.merkle.json` avec la nouvelle racine.

## Règles
- Pourquoi: chaque dérive doit avoir une justification (lien issue/PR) et un impact évalué.
- Quoi: ne jamais inclure des fichiers non déterministes dans le calcul Merkle.
- Comment: reconstruire dans un environnement hermétique (TZ=UTC, PYTHONHASHSEED, SOURCE_DATE_EPOCH, --no-network).

## Dépannage
- Mismatch Merkle: vérifier l’ordre des fichiers, mtime normalisé, et l’exclusion d’artefacts non déterministes.
- Dérive inattendue: comparer `manifest.json` (liste des fichiers, sha256) et rejouer la construction localement.


