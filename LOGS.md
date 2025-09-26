# ProofEngine – LOGS.md

## Run metadata
- Timestamp: 2025-09-26T15:16:07.162531Z
- Commit: b12e57d | Tag: v0.3.0-3-gb12e57d
- OS/Python: Windows 11 | Python 3.13.7
- Model: unknown-model
- PCAP files: 10 | Digest: f6614e19a63dc011f6d7e30516ed58ca4ec54bb5d77be58651812e18ce93852a
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
- 1758898305630_3dcfb8fc.json: plan [pass] test_case
- 1758898305637_88212509.json: verify [fail] test_case
- 1758898305638_4d395bde.json: verify [pass] test_case
- 1758898305642_7ec644ed.json: verify [fail] test_case
- 1758898305646_0bf48a06.json: rollback [fail] test_case
- 1758898305647_35821cba.json: replan [pass] test_case
- 1758898305756_fb321d3c.json: plan [pass] test_case

## Verification summary
- verify pass: 1 | fail: 2
- incidents: 2 | replan_count: 2
- delta_mean: 0.0
- summary.json: {"time": 1758891115.7567375, "all_failed": true}

## Obligations snapshot

## Attestation
- pcap_count: 10
- digest: f6614e19a63dc011f6d7e30516ed58ca4ec54bb5d77be58651812e18ce93852a
- verdicts:
  - 1758891093060_f81ed47f.json: plan [None]
  - 1758891110343_dff30d8c.json: rollback [fail]
  - 1758891115750_d106a6a2.json: replan [fail]
  - 1758898305630_3dcfb8fc.json: plan [pass]
  - 1758898305637_88212509.json: verify [fail]
  - 1758898305638_4d395bde.json: verify [pass]
  - 1758898305642_7ec644ed.json: verify [fail]
  - 1758898305646_0bf48a06.json: rollback [fail]
  - 1758898305647_35821cba.json: replan [pass]
  - 1758898305756_fb321d3c.json: plan [pass]

## Comment (fit probe)
- Direction: hybrid orchestration (stochastic generation inside, deterministic verification outside).
- Value: reduces supervision cost (PCAP journal, attestation, replayability), structures verification.
- Question: do you see interest in large-scale autoformalization, and what minimum bar would you want for a micro-pilot?
