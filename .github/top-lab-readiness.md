# Top-Lab Readiness Epic (6 semaines, scope RegTech/Code)

## Core goals:
- Release guardrails (SBOM=0 High/Critical, cosign attest)
- Nightly Bench + badge + job summary
- Metrics rollup + δ-incidents corr
- Runbook + Operating Contract + Reproducibility
- Bandit/DPP sweep + default tuning
- HS-Tree diagnostics MVP
- IDS sampler MVP
- CVaR in V + policy integration
- 2-morphism policy layer
- Grove Pack (one-pager, script, form drafts)

## Milestones: v0.1.1 (stabilisation), v0.2.0 (features).

## Acceptance Criteria:
- [ ] Nightly Bench workflow runs at 02:00 UTC with job summary
- [ ] Release guardrails enforce SBOM High=0, cosign required
- [ ] Metrics rollup computes weekly coverage_gain, novelty, MDL_drop, δ↔incidents correlation
- [ ] HS-Tree diagnostics for minimal test generation (RegTech/Code)
- [ ] IDS sampler for information-directed exploration
- [ ] CVaR integration in V and selection policy
- [ ] 2-morphism strategy layer with fallback taxonomy
- [ ] Complete documentation suite (Runbook, Operating Contract, Reproducibility)
- [ ] Grove Pack with one-pager, 90s script, form drafts
- [ ] Public Bench Pack v0.1 with signed artifacts

## Success Metrics:
- Incident→rule TTR ≤ 2h
- Audit_cost p95 ≤ baseline−15%
- Determinism drift ≤ 2%
- Coverage gain ≥ +20% vs baselines
- δ-incidents correlation ≥ 0.5
