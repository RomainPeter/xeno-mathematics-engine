# Discovery Engine 2-Cat - Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker (optional, for hermetic execution)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/RomainPeter/discovery-engine-2cat.git
cd discovery-engine-2cat

# Set up environment
make setup

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Quick Demo

```bash
# Run the RegTech demo
make regtech-demo

# Check results
ls out/
# - DCA.jsonl (Decisions, Counter-examples, Actions)
# - J.jsonl (Journal with Merkle hashes)
# - metrics.json (Performance metrics)
```

### Basic Usage

```python
from orchestrator.ae.next_closure import AEExplorer
from orchestrator.ae.oracle import Oracle
from core.state import XState

# Initialize components
state = XState()
oracle = Oracle()
explorer = AEExplorer(state, oracle)

# Run exploration
explorer.run_until_closed(
    budgets_V={"time_ms": 30000},
    thresholds={"coverage_gain_min": 0.05, "novelty_min": 0.2}
)

# Check results
print(f"Implications: {len(state.H)}")
print(f"Counter-examples: {len(state.E)}")
print(f"Rules in K: {len(state.K)}")
print(f"Merkle root: {state.J.get_merkle_root()}")
```

## 🎯 Key Features

### 1. Attribute Exploration (AE)
- **Non-redundancy**: DPP + e-graphs for structural deduplication
- **Minimal completeness**: Next-Closure algorithm
- **Oracle integration**: OPA + static analysis

### 2. E-graph Canonicalization
- **Anti-redundancy**: Structural equivalence detection
- **Witnesses**: Equivalence proofs in journal
- **Rules**: Idempotence, associativity, absorption

### 3. Prompt Governance
- **Contracts**: Structured prompt templates
- **Diversity**: DPP-based selection
- **Validation**: Output schema compliance

### 4. Incident Handling
- **FailReason mapping**: LowNovelty → e-graph forbidden
- **K↑ updates**: Rules from counter-examples
- **Replanning**: Guided by incident analysis

## 📊 Metrics and Monitoring

### Key Metrics
- **Coverage gain**: Improvement over baselines
- **Novelty**: Diversity of generated content
- **Audit cost**: Verification time and resources
- **Incidents**: Failures and their handling

### Monitoring
```bash
# Check metrics
cat out/metrics.json

# View journal
cat out/J.jsonl

# Check Merkle integrity
python scripts/merkle_journal.py
```

## 🔧 Configuration

### Domain Specification
```json
{
  "id": "regtech_code_v1",
  "closure": "exact",
  "oracle_endpoints": {
    "opa_cmd": "opa",
    "rego_pkg": "policy"
  },
  "cost_model": {
    "V_dims": ["time_ms", "audit_cost", "legal_risk", "tech_debt"],
    "units": {"time_ms": "ms", "audit_cost": "USD"}
  }
}
```

### Environment Variables
```bash
export DISCOVERY_SEED=42
export OPA_PATH=/usr/local/bin/opa
export PYTHONHASHSEED=42
```

## 🧪 Testing

```bash
# Run all tests
make discovery-test

# Run specific components
make ae-test
make egraph-test
make bandit-test

# Run determinism test
make determinism-test
```

## 📈 Benchmarking

```bash
# Run RegTech benchmark
make bench-regtech

# Run with baselines
python bench/run.py --suite regtech --baselines react,tot,dspy

# Run ablations
python bench/run.py --suite regtech --ablations egraph,bandit,dpp,incident
```

## 🔒 Security and Attestation

```bash
# Generate SBOM
make sbom-generate

# Security scan
make security-scan

# Docker build
make docker-build

# Full release pipeline
make release-pipeline
```

## 🆘 Troubleshooting

### Common Issues

1. **OPA not found**
   ```bash
   make install-opa
   export OPA_PATH=/usr/local/bin/opa
   ```

2. **Import errors**
   ```bash
   export PYTHONPATH=$(pwd)
   ```

3. **Determinism issues**
   ```bash
   export DISCOVERY_SEED=42
   export PYTHONHASHSEED=42
   ```

### Debug Mode
```bash
# Enable debug logging
export DISCOVERY_DEBUG=1
make regtech-demo
```

## 📚 Next Steps

- [Architecture Guide](ARCHITECTURE.md)
- [Domain Specification](DOMAIN_SPEC.md)
- [Metrics Reference](METRICS.md)
- [Incident Handling](INCIDENT_HANDLING.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make discovery-test`
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
