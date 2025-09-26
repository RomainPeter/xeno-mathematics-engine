# ProofEngine – LOGS.md

## Run metadata
- Timestamp: 2025-09-26T13:59:45.998554Z
- Commit: 675b9eb | Tag: v0.3.0
- OS/Python: Windows 11 | Python 3.13.7
- Model: unknown-model
- PCAP files: 3 | Digest: e29d1ff39141cd272864a9289ae6eb06c5af27242d2731eddea709998b426b3f
- Cache: 33 files (~40 KB)

## Commands & expected outcomes
1) make verify → ping + JSON strict OK
2) make demo → PCAP plan/verify/(incident|replan|success)
3) make audit-pack → out/audit/attestation.json
4) make logs → this file (LOGS.md)

## PCAP timeline (operator → verdict)
- 1758891093060_f81ed47f.json: plan [None] demo_case
- 1758891110343_dff30d8c.json: rollback [fail] demo_case
- 1758891115750_d106a6a2.json: replan [fail] demo_case

## Verification summary
- verify pass: 0 | fail: 0
- incidents: 1 | replan_count: 1
- summary.json: {"time": 1758891115.7567375, "all_failed": true}

## Obligations snapshot

## Attestation
- pcap_count: 3
- digest: e29d1ff39141cd272864a9289ae6eb06c5af27242d2731eddea709998b426b3f
- verdicts:
  - 1758891093060_f81ed47f.json: plan [None]
  - 1758891110343_dff30d8c.json: rollback [fail]
  - 1758891115750_d106a6a2.json: replan [fail]

## Comment (fit probe)
- Direction: hybrid orchestration (stochastic generation inside, deterministic verification outside).
- Value: reduces supervision cost (PCAP journal, attestation, replayability), structures verification.
- Question: do you see interest in large-scale autoformalization, and what minimum bar would you want for a micro-pilot?
