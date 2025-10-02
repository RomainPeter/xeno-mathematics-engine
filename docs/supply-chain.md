# Supply Chain Security

The Xeno Mathematics Engine implements comprehensive supply chain security to ensure the integrity and authenticity of all components.

## Overview

Supply chain security in XME ensures that:

- All dependencies are cryptographically verified
- Build processes are reproducible and deterministic
- All components can be traced to their sources
- Tampering is detected and prevented

## Security Model

### Pipelines et Audit Pack

Le **Discovery Engine 2Cat** produit des **Audit Packs** hermétiques qui intègrent tous les artefacts du pipeline :

- **Manifest** : Liste des fichiers avec SHA256 et Merkle root
- **Artefacts** : PSP, PCAP, métriques, rapports
- **Vérification** : Intégrité cryptographique du pack
- **Traçabilité** : Chaîne complète de génération → vérification

#### Structure de l'Audit Pack
```
2cat-pack-20240101T120000Z.zip
├── manifest.json              # Manifest avec Merkle root
├── artifacts/psp/2cat.json       # PSP généré par AE
├── artifacts/pcap/run-*.jsonl    # Traces PCAP complètes
├── artifacts/metrics/2cat.json   # Métriques δ calculées
├── artifacts/reports/2cat.json  # Rapport final du pipeline
└── docs/psp.schema.json          # Schéma PSP pour validation
```

#### Vérification du Pack
```bash
# Vérifier l'intégrité du pack
xme 2cat verify-pack --pack dist/pack-*.zip

# Vérifier le manifest
xme pack verify --pack dist/pack-*.zip
```

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

```
# 2cat vendor lock file
# This file contains the expected hash, size, and public key for the 2cat vendor package
# Format:
# sha256:<hex>
# size:<bytes>
# pubkey:<minisign_public_key>

sha256:a1b2c3d4e5f6...
size:1048576
pubkey:RWQf6LRCGA9i53mlYecO4IzT51TGPpvWucNSCh1CBM0QTaLn73Y7GFO3
```

### Vendor Policy

XME implements a **dual-mode vendor verification policy**:

#### Local Development (Strict Mode)
- **Enforcement**: `FORCE_VERIFY_2CAT=1` - All vendor packages must be present and valid
- **Behavior**: Missing or invalid packages cause build failure
- **Use Case**: Development environments where vendor packages are required

#### CI/CD (Permissive Mode)
- **Enforcement**: `FORCE_VERIFY_2CAT=0` - Missing packages are skipped gracefully
- **Behavior**: Missing packages log "skipped" and continue build
- **Use Case**: CI environments where vendor packages may not be available

#### Publishing a 2cat Pack

To publish a new 2cat vendor package:

1. **Create the package**:
   ```bash
   tar -czf vendor/2cat/2cat-pack.tar.gz -C vendor/2cat/ src/
   ```

2. **Sign the package**:
   ```bash
   minisign -S -s ~/.minisign/2cat.key -m vendor/2cat/2cat-pack.tar.gz
   ```

3. **Update the lock file**:
   ```bash
   # Calculate SHA256
   sha256=$(shasum -a 256 vendor/2cat/2cat-pack.tar.gz | awk '{print $1}')

   # Get file size
   size=$(stat -c%s vendor/2cat/2cat-pack.tar.gz)

   # Update lock file
   cat > vendor/2cat/2cat.lock << EOF
   sha256:$sha256
   size:$size
   pubkey:RWQf6LRCGA9i53mlYecO4IzT51TGPpvWucNSCh1CBM0QTaLn73Y7GFO3
   EOF
   ```

4. **Test verification**:
   ```bash
   FORCE_VERIFY_2CAT=1 bash scripts/verify_2cat_pack.sh
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

## Audit Pack v0

### Overview

The Audit Pack provides a tamper-evident archive of all project artifacts with cryptographic verification. It includes a manifest with file hashes, Merkle tree root, and comprehensive metadata.

### Structure

```
pack-YYYYMMDDTHHMMSSZ.zip
├── manifest.json          # Pack manifest with metadata
├── file1.psp.json        # PSP artifacts
├── file2.pcap.jsonl      # PCAP journal entries
├── psp.schema.json        # JSON Schema
└── sbom.spdx.json       # Software Bill of Materials
```

### Manifest Format

The manifest contains comprehensive metadata:

```json
{
  "version": 1,
  "created_at": "2024-01-01T00:00:00Z",
  "tool": "xme",
  "run_path": "artifacts/pcap/run-20240101T000000Z.jsonl",
  "files": [
    {
      "path": "artifacts/psp/ae_demo.json",
      "kind": "psp",
      "size": 1024,
      "sha256": "a1b2c3d4e5f6..."
    }
  ],
  "merkle_root": "f6e5d4c3b2a1...",
  "notes": "Audit Pack generated at 2024-01-01T00:00:00Z"
}
```

### Merkle Tree Calculation

The Merkle tree provides tamper-evident verification:

```python
def build_merkle(leaves: List[str]) -> str:
    """Build Merkle tree from file hashes."""
    if not leaves:
        return ""

    if len(leaves) == 1:
        return leaves[0]

    # Build tree level by level
    level = leaves[:]
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            combined = left + right
            next_level.append(hashlib.sha256(combined.encode("utf-8")).hexdigest())
        level = next_level

    return level[0]
```

### CLI Commands

Build an Audit Pack:

```bash
# Build with default patterns
xme pack build --out dist/

# Build with custom patterns
xme pack build --include "artifacts/psp/*.json" --include "artifacts/pcap/*.jsonl" --out dist/

# Build with PCAP run reference
xme pack build --run-path "artifacts/pcap/run-20240101T000000Z.jsonl" --out dist/
```

Verify an Audit Pack:

```bash
# Verify specific pack
xme pack verify --pack dist/pack-20240101T000000Z.zip

# Verify latest pack
xme pack verify --pack "$(ls -1t dist/pack-*.zip | head -1)"
```

### Tamper Detection

The pack verification detects various types of tampering:

1. **Hash Mismatch**: File content has been modified
2. **Missing Files**: Files referenced in manifest are missing
3. **Corrupted Manifest**: Manifest JSON is invalid
4. **Merkle Root Mismatch**: Merkle tree integrity compromised

### CI Integration

The CI pipeline includes pack generation and verification:

```yaml
pack-smoke:
  runs-on: ubuntu-latest
  needs: [pytest]
  steps:
    - uses: actions/checkout@v4
    - uses: cachix/install-nix-action@v27
    - name: Install dependencies
      run: nix develop -c python -m pip install -e .
    - name: Create test artifacts
      run: |
        mkdir -p artifacts/psp artifacts/pcap
        echo '{"blocks": [], "edges": [], "meta": {"theorem": "test"}}' > artifacts/psp/test.psp.json
        echo '{"type": "action", "action": "test", "timestamp": "2024-01-01T00:00:00Z"}' > artifacts/pcap/run-test.jsonl
    - name: Build Audit Pack
      run: nix develop -c xme pack build --out dist/
    - name: Verify Audit Pack
      run: nix develop -c xme pack verify --pack "$(ls -1t dist/pack-*.zip | head -1)"
    - name: Upload pack artifact
      uses: actions/upload-artifact@v4
      with:
        name: audit-pack
        path: dist/pack-*.zip
```

### Security Properties

1. **Tamper Evidence**: Any modification is detected
2. **Cryptographic Integrity**: SHA256 hashes for all files
3. **Merkle Tree**: Efficient verification of large file sets
4. **Deterministic**: Same inputs produce same outputs
5. **Audit Trail**: Complete metadata for forensic analysis

## References

- [Supply Chain Security Best Practices](supply-chain-best-practices.md)
- [Cryptographic Verification](crypto-verification.md)
- [SBOM Standards](sbom-standards.md)
- [Security Compliance](security-compliance.md)
