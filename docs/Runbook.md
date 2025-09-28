# Runbook (Ops)

## Deploy
```bash
docker run --network=none ghcr.io/<org>/<repo>:<tag>
```

## Rollback
Redeploy previous tag; images are signed (cosign verify).

## Incident→Rule Pipeline
1) Monitor incidents in out/metrics.json (incidents.total)
2) Inspect J.jsonl for FailReason
3) Handlers auto-update K and trigger replan; validate new rules in OPA tests

## SLOs
- TTR ≤ 2h
- audit_cost p95 ≤ baseline−15%
- determinism drift ≤ 2%
