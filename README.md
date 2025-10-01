# Xeno Mathematics Engine

A hermetic proof engine for mathematical verification, designed for reproducible and verifiable mathematical reasoning.

[![CI](https://github.com/your-org/xeno-mathematics-engine/workflows/CI/badge.svg)](https://github.com/your-org/xeno-mathematics-engine/actions)

## Overview

The Xeno Mathematics Engine (XME) is a comprehensive system for mathematical proof verification, built with hermetic principles to ensure reproducibility and security. It provides:

- **PSP (Proof Structure Protocol)**: Structured representation of mathematical proofs
- **PCAP (Proof Capability Protocol)**: Capability-based proof verification
- **Supply Chain Security**: Cryptographic verification of all components
- **Hermetic Builds**: Reproducible, deterministic builds using Nix

## Quick Start

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

- [PSP (Proof Structure Protocol)](docs/psp.md) - Learn about proof structure representation
- [PCAP (Proof Capability Protocol)](docs/pcap.md) - Understand capability-based verification
- [Supply Chain Security](docs/supply-chain.md) - Security and verification processes
- [Architecture](docs/architecture.md) - System architecture overview
- [API Reference](docs/api/) - Detailed API documentation

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Status

The project is currently in active development. See our [roadmap](docs/roadmap.md) for planned features and milestones.

## Epic 0 Completion Criteria

- [x] `nix develop` works correctly
- [x] `flake.lock` committed
- [x] Pre-commit hooks block CI correctly
- [x] Pytest tests pass
- [x] Docker image executes `xme --help`
- [x] SBOM generated in CI with Syft
- [x] Script `verify_2cat` works (when pack present)
- [x] README with CI badge

## Architecture Decisions

### Naming Consistency
- Unified "xme" naming throughout (CLI, package, workflow)
- Avoided "bfk/bfk" naming conflicts

### Deterministic JSON
- Using `orjson` with `OPT_SORT_KEYS` for deterministic JSON
- Roundtrip tests for PSP and PCAP

### PSP Validation
- NetworkX enforces DAG properties
- Hooks for additional constraints (typing, contexts)
- Normalized "kinds" via Enum

### PCAP Schema
- Minimal obligation schema (S0) defined
- Required keys: `policy_id`, `invariant_id`, `result`, `proof_ref`

### Supply Chain Security
- Minisign public key required in `vendor/2cat/2cat.lock`
- CI check that only fails if all three files exist and verification fails

### Infrastructure vs Logic Separation
- Epic 0 focuses on infrastructure, not orchestrator/engines logic
- Placeholder directories with README.md files
- No logic implementation until PSP/PCAP and CI are solid

## Future Enhancements

### Planned Features
- **Distributed Verification**: Support for distributed proof verification
- **Machine Learning Integration**: ML-based proof strategy selection
- **Advanced Proof Methods**: Integration with Lean, Coq, and other provers
- **Visual Proof Designer**: GUI for proof construction

### Integration Points
- **Cloud Integration**: Integration with cloud services
- **Monitoring Systems**: Integration with monitoring tools
- **Notification Systems**: Integration with notification services
- **Analytics**: Integration with analytics platforms