# Verifier v0.1 - Hermetic Docker Runner

## Overview

The Verifier provides hermetic verification of Proof-Carrying Actions (PCAPs) using Docker containers with strict isolation and resource limits.

## Features

### Isolation
- **No network access**: `--network=none`
- **CPU limit**: `--cpus=1`
- **Memory limit**: `-m 512m`
- **Process limit**: `--pids-limit=256`
- **Read-only filesystem**: `--read-only`
- **Temporary filesystems**: `--tmpfs /tmp --tmpfs /run`

### Security
- Non-root user execution
- Minimal base image (python:3.11-slim)
- No network egress capability
- Resource quotas prevent DoS

### Attestation
- **cosign signing**: Local signing with private key
- **in-toto provenance**: Image digest, PCAP hashes, timestamps
- **Fallback signatures**: When cosign unavailable

## Usage

### Local Runner
```bash
python scripts/verifier.py --pcap examples/v0.1/pcap/ex1.json --runner local
```

### Docker Runner
```bash
python scripts/verifier.py --pcap examples/v0.1/pcap/ex1.json --runner docker
```

### Orchestrator with Docker Verifier
```bash
python orchestrator/skeleton_llm.py --plan plans/plan-hello.json --state state/x-hello.json --verifier docker
```

## CLI Flags

- `--pcap`: PCAP file(s) to verify (can be repeated)
- `--runner`: Runner mode (`local` or `docker`)
- `--out`: Output directory (default: `artifacts/verifier_out`)
- `--timeout`: Timeout in seconds (default: 300)
- `--sign`: Sign audit pack with cosign
- `--cosign-key`: Path to cosign private key

## Output Files

### Audit Pack
- `audit_pack.zip`: Complete verification package
- `attestation.json`: Combined attestation for all PCAPs
- `provenance.json`: in-toto provenance metadata

### Individual Attestations
- `{pcap_name}_attestation.json`: Per-PCAP attestation
- `audit_pack.sig`: cosign signature (if signing enabled)

## Docker Image

### Build
```bash
docker build -t proofengine/verifier:0.1.0 -f Dockerfile.verifier .
```

### Contents
- Python 3.11-slim base
- Dependencies from `requirements.lock`
- OPA binary for policy checks
- Verifier scripts and policies
- Non-root user execution

## CI Integration

### Linux-only Jobs
- `demo-s1-docker`: Demo with Docker verifier
- `expected-fail-docker`: Policy violation test
- `build`: Stabilized build with pip cache

### macOS Limitation
- Limited to non-docker tests
- Docker jobs run only on ubuntu-latest
- Prevents macOS Docker issues

## Security Model

### Network Isolation
- No network access in container
- Egress test validates blocking
- Prevents data exfiltration

### Resource Limits
- CPU: 1 core maximum
- Memory: 512MB maximum
- Processes: 256 maximum
- Prevents resource exhaustion

### Filesystem
- Read-only root filesystem
- Temporary filesystems for /tmp and /run
- Workspace mounted read-only
- Output directory writable

## Attestation Schema

### Combined Attestation
```json
{
  "version": "0.1.0",
  "ts": "2024-01-01T00:00:00Z",
  "pcap_count": 1,
  "attestations": [...],
  "digest": "sha256:..."
}
```

### Provenance
```json
{
  "version": "0.1.0",
  "ts": "2024-01-01T00:00:00Z",
  "image_digest": "sha256:...",
  "pcap_hashes": ["sha256:..."],
  "audit_pack_hash": "sha256:..."
}
```

## Limitations v0.1

- Single PCAP verification per container
- No parallel verification
- Limited to Linux containers
- cosign signing requires local key
- No remote attestation

## Future Enhancements

- Parallel PCAP verification
- Remote cosign signing
- Multi-architecture support
- Enhanced provenance
- Integration with external attestation services
