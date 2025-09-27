# Orchestrator Skeleton v0.1

## Quick Start

```bash
# Setup
python -m venv .venv
. .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.lock

# Validate schemas
make validate

# Run demo
make demo-s1

# Check results
cat metrics.json
cat state/x-hello-updated.json
```

## Architecture

```
Plan (Π) → Orchestrator → PCAP → Verifier → Journal (J)
    ↓           ↓          ↓        ↓         ↓
  Steps    Execute    Attest   Hermetic   Chain
```

## Commands

- `make validate` - Schema validation
- `make fmt` - Format code
- `make demo-s1` - Run 5 S1 tasks
- `python scripts/pcap.py new <file> --action <name> --target <path>`
- `python scripts/verifier.py <pcap_file>`
- `python orchestrator/skeleton.py --plan <plan> --state <state>`

## Security

- Verifier: sandboxed, timeout 45s, no network
- PCAP: context_hash integrity, signature verification
- SBOM: `sbom.json` with pinned dependencies

## Metrics

- Accept rate: % of successful steps
- Replans: count of rollback/replan cycles  
- Time: total execution time (ms)
- δ: delta between X_before/X_after

## Known Limitations

- LLM: stub implementation (70% success rate)
- Verifier: not OCI/Wasm yet
- δ: not calibrated on real data
- S1: reduced corpus (5 tasks)

## Next: Sprint C

- Real LLM adapter with contracts
- Hardened verifier (OCI/Wasm)
- S2 corpus (15 tasks)
- δ calibration
- Governance rules
