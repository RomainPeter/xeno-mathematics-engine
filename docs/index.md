# Xeno Mathematics Engine

A hermetic proof engine for mathematical verification, designed for reproducible and verifiable mathematical reasoning.

## Overview

The Xeno Mathematics Engine (XME) is a comprehensive system for mathematical proof verification, built with hermetic principles to ensure reproducibility and security. It provides:

- **PSP (Proof Structure Protocol)**: Structured representation of mathematical proofs
- **PCAP (Proof-Carrying Actions)**: Action verification with embedded proofs
- **Supply Chain Security**: Cryptographic verification of all components
- **Hermetic Builds**: Reproducible, deterministic builds using Nix

## Quick Start

### Discovery Engine 2Cat Pipeline

Le pipeline unifié AE+CEGIS avec pack hermétique :

```bash
# Exécuter le pipeline complet
xme 2cat run --config config/pipelines/default.yaml

# Vérifier le pack généré
xme 2cat verify-pack --pack dist/pack-*.zip

# Générer une configuration personnalisée
xme 2cat config --template
```

### Development Environment

```bash
# Enter development environment
make dev

# Run tests
make test

# Build the CLI
make build
```

### Docker Usage

```bash
# Build Docker image
make docker

# Run the CLI
docker run --rm xme/dev:latest --help
```

## Architecture

XME is built around several core components:

- **Orchestrator**: Coordinates proof verification workflows
- **Engines**: Specialized proof verification engines
- **Methods**: Various proof methods (AE, CEGIS, etc.)
- **Persistence**: Storage and retrieval of proofs and data
- **Policy**: Security and verification policies

## Key Features

### 🔒 Hermetic Security
- All dependencies are cryptographically verified
- Reproducible builds using Nix
- Supply chain integrity verification

### 🧮 Mathematical Rigor
- Formal verification of proof structures
- DAG validation for proof dependencies
- Capability-based access control

### 🚀 Performance
- Optimized proof verification
- Parallel processing capabilities
- Efficient storage and retrieval

### 🔧 Developer Experience
- Comprehensive CI/CD pipeline
- Docker support for easy deployment
- Extensive documentation and examples

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/xeno-mathematics-engine.git
   cd xeno-mathematics-engine
   ```

2. **Enter development environment**
   ```bash
   make dev
   ```

3. **Run tests**
   ```bash
   make test
   ```

4. **Build the CLI**
   ```bash
   make build
   ```

## Documentation

### Discovery Engine 2Cat Pipeline

Le pipeline unifié **Discovery Engine 2Cat** combine Attribute Exploration (AE) et Counter-Example Guided Inductive Synthesis (CEGIS) pour produire des preuves vérifiables avec un pack hermétique.

#### Fonctionnalités
- **Pipeline unifié** : AE (algo réel) → CEGIS (v0) → Vérification PSP S1 → Métriques δ → Audit Pack
- **Configuration YAML** : Configuration flexible et versionnée
- **Pack hermétique** : Audit Pack avec manifest, Merkle root et vérification d'intégrité
- **Métriques intégrées** : Calcul automatique des δ (adjunction defect)
- **Logging PCAP** : Traçabilité complète des actions et vérifications

#### Utilisation
```bash
# Configuration par défaut
xme 2cat run --config config/pipelines/default.yaml

# Configuration personnalisée
xme 2cat config --template
# Éditer le fichier généré
xme 2cat run --config my-config.yaml

# Vérification du pack
xme 2cat verify-pack --pack dist/pack-*.zip
```

#### Structure du pack
```
dist/
├── 2cat-pack-20240101T120000Z.zip
│   ├── manifest.json          # Manifest avec Merkle root
│   ├── artifacts/psp/2cat.json    # PSP généré
│   ├── artifacts/pcap/run-*.jsonl # Traces PCAP
│   └── docs/psp.schema.json      # Schéma PSP
```

### Core Components

- [PSP (Proof Structure Protocol)](psp.md) - Learn about proof structure representation
- [PCAP (Proof-Carrying Actions)](pcap.md) - Understand action verification with embedded proofs
- [Metrics & δ](metrics.md) - Adjunction defect calculation and analysis
- [Supply Chain Security](supply-chain.md) - Security and verification processes
- [Architecture](architecture.md) - System architecture overview
- [API Reference](api/) - Detailed API documentation

## Contributing

We welcome contributions! Please see our [Contributing Guide](contributing.md) for details on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](license.md) file for details.

## Status

![CI](https://github.com/your-org/xeno-mathematics-engine/workflows/CI/badge.svg)

The project is currently in active development. See our [roadmap](roadmap.md) for planned features and milestones.
