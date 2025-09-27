# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-01-27

### Added
- **LLM Adapter v0.1**: Integration with Kimi K2 via OpenRouter
  - Auto-consistency with n=3 retries
  - PromptContract schema validation
  - Local caching for offline replay
- **Hermetic Verifier v0.1**: Docker-based verification
  - No-network sandbox (`--network=none`)
  - Resource quotas (CPU: 1, Memory: 512MB, PIDs: 256)
  - Read-only filesystem with tmpfs for /tmp and /run
  - Cosign attestation support
- **Shock Ladder S2**: Hostile task corpus
  - 10+ adversarial test cases
  - Expected failure demonstrations
  - Incident-to-rule governance
- **δ Calibration**: Defect metric calculation
  - Multi-dimensional delta measurement
  - Correlation analysis with incidents
  - Jupyter notebook for calibration
- **Supply Chain Security**:
  - SBOM generation (SPDX 2.3)
  - Cosign signature verification
  - in-toto provenance
  - OPA policy enforcement
- **CI/CD Enhancements**:
  - Linux-only Docker jobs
  - Expected-fail demonstrations
  - Attestation verification workflow
  - Simplified smoke tests

### Changed
- Simplified CI workflows for better stability
- Updated dependency pinning with `requirements.lock`
- Enhanced security policies with OPA rules

### Security
- Added cosign public key for artifact verification
- Implemented hermetic Docker execution
- Enhanced supply chain attestations
- Added vulnerability scanning (Trivy/Grype)

## [0.1.0] - 2025-01-26

### Added
- Initial Proof Engine for Code architecture
- JSON Schema definitions for X, J, PCAP, Π, FailReason
- Basic CLI tools and orchestration
- Pre-commit hooks and code quality tools
- Initial test corpus and examples
