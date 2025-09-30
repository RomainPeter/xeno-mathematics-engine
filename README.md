# xeno-mathematics-engine

Badges
- CI Hardening: ![CI Hardening](https://github.com/OWNER/REPO/actions/workflows/ci-harden.yml/badge.svg)
- Pack Verify: ![Pack Verify](https://github.com/OWNER/REPO/actions/workflows/pack-verify.yml/badge.svg)
- Orchestrator E2E: ![Orchestrator E2E](https://github.com/OWNER/REPO/actions/workflows/orchestrator-e2e.yml/badge.svg)

![CI](https://github.com/RomainPeter/discovery-engine-2cat/actions/workflows/ci.yml/badge.svg)
![Nightly Bench](https://github.com/RomainPeter/discovery-engine-2cat/actions/workflows/nightly-bench.yml/badge.svg)
![Gate Merge](https://github.com/RomainPeter/discovery-engine-2cat/actions/workflows/gate-merge.yml/badge.svg)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Building a telescope to produce and observe alien Mathematics. Xeno-mathematics as an AI enhancement to our mathematical understanding.

## Quickstart

- Dev shell (Nix): `nix develop`
- Pré-commit: `pre-commit install`
- Lancer CLI minimale: `bfk version`
- Vérifier vendor 2cat offline: `bfk verify-vendor`

## Ressources CI & Sécurité

- Politique CI et portes: voir `docs/CI.md`
- Politique de dérive (baseline Merkle): voir `docs/DRIFT_POLICY.md`

## Architecture

Ce repository contient l'agent de découverte basé sur l'Architecture Unifiée v0.1, utilisant le Proof Engine comme dépendance versionnée.

### Structure

```
discovery-engine-2cat/
├── external/
│   └── proof-engine-core/          # Submodule @ tag v0.1.0
├── orchestrator/                   # Orchestrateur principal
├── methods/                        # Méthodes AE/CEGIS/e-graph
├── domain/                         # Domain adapters
├── schemas/                        # JSON Schemas v0.1
├── bench/                          # Benchmarks + baselines
├── ci/                            # CI/CD + attestations
└── prompts/                       # Micro-prompts LLM
```

### Composants

- **AE (Attribute Exploration)**: Next-closure algorithm avec oracle Verifier
- **CEGIS**: Counter-Example Guided Inductive Synthesis
- **E-graphs**: Canonicalisation et anti-redondance structurelle
- **Sélection**: Bandit contextuel, MCTS, Pareto
- **Domain Adapters**: RegTech/Code, etc.

### Utilisation

#### CLI unifiée (T17)

```bash
# Pack operations
pefc pack build --pipeline config/pipelines/bench_pack.yaml
pefc pack verify --zip dist/*.zip --strict
pefc pack manifest --zip dist/*.zip --print
pefc pack sign --in dist/*.zip --provider cosign

# Configuration
pefc --config config/pack.yaml --json-logs pack build
```

#### CI Pack smoke-test (T19)

Le CI garantit en continu l'absence de régression dans la construction et la vérification des packs :

```bash
# Test local du workflow CI
python test_ci_workflow.py

# Vérification des doublons
python scripts/check_zip_duplicates.py dist/dist/*.zip

# Vérification complète
pefc pack verify --zip dist/dist/*.zip --strict
```

**Fonctionnalités CI :**
- ✅ Construction automatique avec `pefc pack build`
- ✅ Détection des doublons d'arcnames dans le ZIP
- ✅ Vérification stricte manifest/SHA256/Merkle
- ✅ Tests sur Python 3.10, 3.11, 3.12
- ✅ Artefacts : ZIP, manifest.json, verify.json, merkle_root.txt
- ✅ Résumé CI avec métriques détaillées

**Déclencheurs :**
- Push sur `main`
- Pull requests
- Tags `v*`

#### Makefile (compatible)

```bash
# Tests
make ae-test          # Test AE Next-Closure
make egraph-test      # Test E-graph canonicalization
make bandit-test      # Test bandit/DPP selection
make ci-test          # Test CI components

# Pack operations (utilise pefc CLI)
make public-bench-pack # Build pack avec pipeline par défaut
make verify-pack      # Vérifier pack avec signature
make pack-manifest    # Afficher manifest
make pack-sign        # Signer pack

# Démo
make discovery-demo   # Démo complète

# CI Pipeline
make ci-full          # Pipeline CI complet
make hermetic-test    # Test runner hermétique
make merkle-test      # Test journal Merkle
make attestation      # Génération attestation
```

### Dépendances

- **proof-engine-core**: Noyau stable (PCAP, runner hermétique, attestations)
- **Python 3.10+**: Runtime
- **OPA**: Oracle pour vérification
- **Static Analysis**: Outils d'analyse statique

### Versioning

- **discovery-engine**: v0.x (exploration et orchestration)
- **proof-engine-core**: v0.x (noyau stable)
- Compatibilité: `proof-engine-core>=0.1.0,<0.2.0`

## Développement

### Migration depuis proof-engine-for-code

Ce repository a été créé en migrant les composants d'exploration depuis le Proof Engine principal pour permettre un développement indépendant et accéléré.

### Garde-faus

- Aucune modification directe de `proof-engine-core`
- Toute évolution du core → PR sur proof-engine-core → nouveau tag → bump submodule
- Attestations distinctes par repository
- Versionnage coordonné avec contraintes de compatibilité

## CI/CD

### Workflows

- **CI**: Tests sur Python 3.10, 3.11, 3.12 avec matrix
- **Attestation**: Génération d'attestations avec Merkle root
- **Hermetic Runner**: Exécution reproductible avec enregistrement

### Artifacts

- **Merkle Root**: Hachage d'intégrité du journal
- **Attestation**: Signature des composants
- **Test Results**: Résultats des tests avec couverture

## License

Voir LICENSE pour les détails.