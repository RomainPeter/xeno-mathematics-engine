# Benchmark Public - 2-Category Transformations

## Objectif
Reproduire le benchmark public en local (hermétique) et vérifier les artefacts signés.

## Étapes

### 1. Benchmark baseline et active
```bash
make bench-baseline && make bench-active
```

### 2. Calibration des poids δ
```bash
make delta-calibrate
```
Produit `configs/weights.json` et rapport JSON.

### 3. Reproduction publique
```bash
make repro-public
```
Pack zip + provenance + signature si `COSIGN_KEY` défini.

### 4. Vérification des signatures
```bash
cosign verify-blob --key .github/security/cosign.pub --signature artifacts/bench_public/audit.sig artifacts/bench_public/audit_pack.zip
```

## Optimisations overhead

### Skips
- Ne lancer OPA/pytest que si diff détecté
- Cache scans: si hash(requirements.lock) inchangé, réutiliser SBOM

### Early-gate
- Si FailReason non mappé → pas d'appel selector

### Batch
- Regrouper tests/OPA dans un runner unique

## Métriques cibles

- **Success Rate Delta S2** ≥ +10 pts vs baseline
- **Overhead** ≤ 12% (actuel 18.2% → optimiser)
- **Corr(δ, incidents)** ≥ 0.6 sur S1+S2
- **Repro 1-commande** en environnement hermétique + cosign verify OK
