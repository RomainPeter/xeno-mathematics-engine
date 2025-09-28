# Discovery Engine 2-Cat

![CI](https://github.com/RomainPeter/discovery-engine-2cat/actions/workflows/ci.yml/badge.svg)
![Nightly Bench](https://github.com/RomainPeter/discovery-engine-2cat/actions/workflows/nightly-bench.yml/badge.svg)
![Gate Merge](https://github.com/RomainPeter/discovery-engine-2cat/actions/workflows/gate-merge.yml/badge.svg)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Orchestrateur 2-cat, AE/CEGIS, e-graphs, bandit/MCTS, domain adapters, benchmarks.

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

```bash
# Tests
make ae-test          # Test AE Next-Closure
make egraph-test      # Test E-graph canonicalization
make bandit-test      # Test bandit/DPP selection
make ci-test          # Test CI components

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