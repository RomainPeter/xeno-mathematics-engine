# dancing-machines — Usage Guide

## Quick Start (10 lines)

```bash
# 1. Setup
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env  # Add OPENROUTER_API_KEY and OPENROUTER_MODEL (moonshotai/kimi-k2:free)

# 3. Validate & Demo
make validate        # Schema validation
make demo-s1        # 5 S1 tasks (rename, off-by-one, API, test, lint)
```

## Structure

```
orchestrator/       # Plan-Execute-Replan loop
scripts/           # CLI tools (pcap, verifier, metrics)
corpus/s1/         # 5 Shock Ladder tasks
specs/v0.1/        # JSON schemas (J, X, PCAP, Π, FailReason)
examples/v0.1/     # Schema examples + round-trip tests
```

## Artifacts

- `metrics.json` — Accept rate, time, δ metrics
- `state/x-hello-updated.json` — Final cognitive state
- `sbom.json` — Software Bill of Materials
- `artifacts/audit_pack_*.zip` — Complete audit bundle

## Commands

- `make validate` — Schema validation
- `make demo-s1` — Run 5 S1 tasks  
- `python scripts/pcap.py new <file> --action <name> --target <path>`
- `python scripts/verifier.py <pcap_file>`
- `python orchestrator/skeleton.py --plan <plan> --state <state>`

**Proof**: Accept rate 100% (5/5), Time 17ms, Journal chain OK
