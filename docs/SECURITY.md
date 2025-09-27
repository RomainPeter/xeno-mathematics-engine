# Security Policy

## Supply Chain Security

This project implements comprehensive supply chain security measures to ensure the integrity and authenticity of all artifacts.

### Docker Image Security

- **Pinned Digests**: All Docker images are pinned by SHA256 digest
- **Verification**: CI verifies that no floating tags are used
- **Base Images**: Only trusted base images from official repositories

### Dependency Security

- **Hash Verification**: All dependencies are installed with `--require-hashes`
- **Lock File**: `requirements.lock` contains cryptographic hashes for all packages
- **Vulnerability Scanning**: Trivy and Grype scans on every build

### Attestation & Signing

- **Cosign Signatures**: All audit packs are signed with cosign
- **Public Key**: Available in `.github/security/cosign.pub`
- **Verification**: CI verifies signatures on tag releases
- **in-toto Provenance**: Supply chain attestations for all artifacts

### Policy Enforcement

- **OPA Policies**: Rego policies for semver and changelog compliance
- **Expected Failures**: Policy violations are demonstrated in CI
- **Automated Checks**: All policies are enforced automatically

## Vulnerability Management

### Scanning

- **Filesystem**: Trivy scans all source code for vulnerabilities
- **Container Images**: Both Trivy and Grype scan Docker images
- **SARIF Upload**: Results uploaded to GitHub Security tab

### Severity Levels

- **CRITICAL**: Build fails immediately
- **HIGH**: Build fails unless waived
- **MEDIUM/LOW**: Reported but don't fail build

### Waivers

To waive a vulnerability:

1. Create issue with `security-waiver` label
2. Provide justification and mitigation plan
3. Add to `.grype.yaml` with waiver details
4. Get approval from security team

## Reporting Security Issues

### Private Disclosure

For security vulnerabilities, please:

1. **DO NOT** create public issues
2. Email security team directly
3. Include detailed reproduction steps
4. Allow 90 days for response

### Public Issues

For non-security issues:

1. Create public issue with appropriate labels
2. Provide detailed description
3. Include reproduction steps if applicable

## Security Contacts

- **Security Team**: security@example.com
- **PGP Key**: Available in repository
- **Response Time**: 48 hours for critical issues

## Compliance

This project follows:

- **SLSA Level 2**: Build provenance and source verification
- **SPDX 2.3**: Software Bill of Materials
- **in-toto**: Supply chain integrity framework
- **OWASP**: Secure coding practices

## Incident Response

### Security Incidents

1. **Immediate**: Disable affected systems
2. **Assessment**: Determine scope and impact
3. **Containment**: Prevent further damage
4. **Recovery**: Restore secure state
5. **Post-mortem**: Document lessons learned

### Communication

- **Internal**: Security team notification
- **External**: Coordinated disclosure timeline
- **Public**: Security advisory if needed

## Security Metrics

- **Vulnerability Count**: Tracked in security dashboard
- **Scan Coverage**: 100% of codebase and dependencies
- **Response Time**: < 48 hours for critical issues
- **Compliance**: Quarterly security reviews
