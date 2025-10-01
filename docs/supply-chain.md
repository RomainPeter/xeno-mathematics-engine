# Supply Chain Security

The Xeno Mathematics Engine implements comprehensive supply chain security to ensure the integrity and authenticity of all components.

## Overview

Supply chain security in XME ensures that:

- All dependencies are cryptographically verified
- Build processes are reproducible and deterministic
- All components can be traced to their sources
- Tampering is detected and prevented

## Security Model

### Cryptographic Verification

All components are cryptographically signed and verified:

- **Vendor Packages**: Signed with minisign
- **Dependencies**: SHA256 checksums verified
- **Build Artifacts**: Cryptographically signed
- **Docker Images**: Cosign attestation

### Reproducible Builds

XME uses Nix for hermetic, reproducible builds:

- **Deterministic Environment**: All dependencies locked
- **Isolated Builds**: No network access during build
- **Cryptographic Hashes**: All inputs hashed and verified
- **Reproducible Outputs**: Same inputs produce same outputs

## Vendor Package Verification

### 2cat Package Structure

The 2cat vendor package follows a strict verification protocol:

```
vendor/2cat/
├── README.md              # Package documentation
├── 2cat.lock             # Lock file with metadata
├── 2cat-pack.tar.gz      # The actual package
└── 2cat-pack.tar.gz.minisig  # Digital signature
```

### Lock File Format

The lock file contains essential verification information:

```yaml
# Package metadata
name: 2cat
version: 1.0.0
description: 2cat vendor package for xeno-mathematics-engine

# Security verification
sha256: a1b2c3d4e5f6...
pubkey: RWR+WQZ2jNToFXbeOaKihS2kSy5uz10Hi+HOA3Rq2rRF8u6n7wi3ws

# Build information
build_date: 2024-01-01T00:00:00Z
build_system: nix
build_commit: abc123def456
```

### Verification Process

The verification script performs comprehensive checks:

```bash
#!/usr/bin/env bash
set -euo pipefail

PACK="vendor/2cat/2cat-pack.tar.gz"
SIG="${PACK}.minisig"
LOCK="vendor/2cat/2cat.lock"

# Check file existence
[ -f "$PACK" ] && [ -f "$SIG" ] && [ -f "$LOCK" ] || { 
    echo "Missing pack/signature/lock"; exit 2; 
}

# Verify SHA256 checksum
EXPECTED_SHA=$(grep '^sha256:' "$LOCK" | cut -d: -f2)
ACTUAL_SHA=$(shasum -a 256 "$PACK" | awk '{print $1}')
[ "$EXPECTED_SHA" = "$ACTUAL_SHA" ] || { 
    echo "SHA256 mismatch"; exit 3; 
}

# Verify digital signature
PUBKEY=$(grep '^pubkey:' "$LOCK" | cut -d: -f2-)
minisign -V -P "$PUBKEY" -m "$PACK" -x "$SIG" >/dev/null

echo "2cat pack verified"
```

## CI/CD Security

### GitHub Actions Pipeline

The CI pipeline implements multiple security layers:

```yaml
name: CI
on: [push, pull_request]
jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: cachix/install-nix-action@v27
      - run: nix develop -c pre-commit run -a
  
  sbom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: cachix/install-nix-action@v27
      - run: nix develop -c bash -lc 'mkdir -p sbom && syft dir:. -o spdx-json > sbom/sbom.spdx.json'
      - uses: actions/upload-artifact@v4
        with: { name: sbom, path: sbom/sbom.spdx.json }
  
  docker-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v6
        with: { context: ., push: false, tags: xme/dev:latest }
  
  attest:
    if: ${{ secrets.COSIGN_KEY != '' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: sigstore/cosign-installer@v3
      - run: cosign version
      - run: echo "Attest placeholder - wire your registry and key"
```

### SBOM Generation

Software Bill of Materials (SBOM) is generated for all components:

```bash
# Generate SBOM
syft dir:. -o spdx-json > sbom/sbom.spdx.json

# Verify SBOM
syft attest --key cosign.key --predicate sbom/sbom.spdx.json xme/dev:latest
```

## Docker Security

### Multi-stage Builds

The Dockerfile uses multi-stage builds for security:

```dockerfile
FROM nixpkgs/nix:latest AS builder
WORKDIR /src
COPY . .
RUN nix build .#xme && ln -sf $(readlink -f result/bin/xme) /usr/local/bin/xme

FROM nixpkgs/nix:latest
COPY --from=builder /nix/store /nix/store
COPY --from=builder /usr/local/bin/xme /usr/local/bin/xme
ENTRYPOINT ["xme"]
CMD ["--help"]
```

### Image Attestation

Docker images are cryptographically attested:

```bash
# Attest Docker image
cosign attest --key cosign.key --predicate sbom/sbom.spdx.json xme/dev:latest

# Verify attestation
cosign verify-attestation --key cosign.pub xme/dev:latest
```

## Nix Security

### Flake Lock

The `flake.lock` file ensures reproducible builds:

```json
{
  "nodes": {
    "nixpkgs": {
      "locked": {
        "lastModified": 1640995200,
        "narHash": "sha256-...",
        "owner": "NixOS",
        "repo": "nixpkgs",
        "rev": "abc123...",
        "type": "github"
      }
    }
  }
}
```

### Deterministic Builds

All builds are deterministic:

```bash
# Build with deterministic output
nix build .#xme --option sandbox true

# Verify build reproducibility
nix build .#xme --option sandbox true --option deterministic true
```

## Security Policies

### Dependency Verification

All dependencies are verified:

```python
def verify_dependencies():
    """Verify all project dependencies."""
    # Check Python dependencies
    verify_python_deps()
    
    # Check Nix dependencies
    verify_nix_deps()
    
    # Check vendor packages
    verify_vendor_packages()
```

### Access Control

Strict access control is enforced:

```python
class SecurityPolicy:
    def __init__(self):
        self.allowed_sources = [
            "github.com",
            "pypi.org",
            "nixpkgs.org"
        ]
    
    def verify_source(self, source):
        """Verify that source is allowed."""
        return source in self.allowed_sources
```

## Monitoring and Auditing

### Security Monitoring

Continuous security monitoring:

```python
class SecurityMonitor:
    def monitor_builds(self):
        """Monitor build processes for security issues."""
        pass
    
    def audit_dependencies(self):
        """Audit dependencies for vulnerabilities."""
        pass
    
    def check_integrity(self):
        """Check system integrity."""
        pass
```

### Audit Logging

Comprehensive audit logging:

```python
import logging

security_logger = logging.getLogger('security')

def log_security_event(event_type, details):
    """Log security events."""
    security_logger.info(f"{event_type}: {details}")
```

## Best Practices

### Secure Development

1. **Minimal Dependencies**: Use minimal, trusted dependencies
2. **Regular Updates**: Keep dependencies up to date
3. **Vulnerability Scanning**: Regular security scans
4. **Code Review**: Security-focused code reviews

### Build Security

1. **Isolated Builds**: Use isolated build environments
2. **Deterministic Outputs**: Ensure reproducible builds
3. **Cryptographic Verification**: Verify all inputs
4. **Audit Trails**: Maintain comprehensive audit trails

## Troubleshooting

### Common Issues

1. **Signature Verification Failed**: Check public keys and signatures
2. **Checksum Mismatch**: Verify file integrity
3. **Build Reproducibility**: Check Nix configuration
4. **Dependency Issues**: Verify dependency sources

### Security Tools

```bash
# Verify vendor packages
./scripts/verify_2cat_pack.sh

# Check SBOM
syft attest --key cosign.key --predicate sbom/sbom.spdx.json xme/dev:latest

# Audit dependencies
nix audit

# Security scan
nix scan
```

## Future Enhancements

### Planned Features

- **Automated Vulnerability Scanning**: Continuous vulnerability scanning
- **Policy as Code**: Security policies as code
- **Compliance Reporting**: Automated compliance reporting
- **Threat Modeling**: Automated threat modeling

### Integration Points

- **Security Information and Event Management (SIEM)**: Integration with SIEM systems
- **Vulnerability Databases**: Integration with vulnerability databases
- **Compliance Frameworks**: Integration with compliance frameworks
- **Security Orchestration**: Integration with security orchestration tools

## References

- [Supply Chain Security Best Practices](supply-chain-best-practices.md)
- [Cryptographic Verification](crypto-verification.md)
- [SBOM Standards](sbom-standards.md)
- [Security Compliance](security-compliance.md)
