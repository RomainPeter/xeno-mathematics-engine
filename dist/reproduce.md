# Discovery Engine 2‑Cat — Reproduction Instructions

## Prerequisites

- Python 3.11+
- Docker 24.0+
- Git

## Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/discovery-engine-2cat.git
cd discovery-engine-2cat
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Reproduction

1. Set deterministic seeds:
```bash
export DISCOVERY_SEED=42
export PYTHONHASHSEED=42
```

2. Run benchmark:
```bash
make regtech-demo
```

3. Verify results:
```bash
make determinism
```

4. Check metrics:
```bash
cat out/metrics.json
```

## Verification

### Merkle Root
The Merkle root should match the provided value:
```bash
cat out/journal/merkle.txt
```

### SBOM
The SBOM should show 0 High/Critical vulnerabilities:
```bash
cat out/sbom.json
```

### Metrics
Expected metrics ranges:
- Coverage gain: 0.18-0.25
- Novelty average: 0.19-0.22
- Audit cost p95: 950-1000ms

## Troubleshooting

### Common Issues
1. **Seed mismatch**: Ensure PYTHONHASHSEED is set
2. **Docker issues**: Ensure Docker is running
3. **Permission issues**: Check file permissions

### Support
- GitHub Issues: https://github.com/your-org/discovery-engine-2cat/issues
- Email: contact@your-org.com

## License

This benchmark pack is released under the MIT License.
