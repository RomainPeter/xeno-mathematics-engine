#!/usr/bin/env python3
"""
Create GitHub Issues for v0.1.1 hardening
"""

issues = [
    {
        "title": "v0.1.1: Determinism bounds test",
        "body": """## Determinism bounds test

**Objective**: Ensure variance V_actual ≤ 2%, drift seeds=0

**Acceptance Criteria**:
- [ ] 3 identical runs with same seed → identical Merkle root
- [ ] Variance V_actual ≤ 2% across runs
- [ ] No seed drift (seeds=0)
- [ ] Test marked as 'determinism' in CI

**Implementation**:
- Update `scripts/determinism_test.py` with bounds checking
- Add CI gate for determinism test
- Generate determinism report in artifacts

**Success Metrics**:
- Determinism score ≥ 0.95
- Merkle root consistency = 100%
- Variance ≤ 2%""",
        "labels": ["v0.1.1", "determinism", "testing"],
    },
    {
        "title": "v0.1.1: E-graph rules + tests",
        "body": """## E-graph rules + tests

**Objective**: Ratio dédup ≥ 0.9; ajouter 2 règles sûres supplémentaires (commutations gardées) + tests

**Acceptance Criteria**:
- [ ] E-graph deduplication ratio ≥ 0.9
- [ ] Add 2 safe rules (guarded commutations)
- [ ] Comprehensive test coverage for e-graph rules
- [ ] Performance benchmarks for canonicalization

**Implementation**:
- Add guarded commutation rules to `methods/egraph/rules.py`
- Implement deduplication ratio measurement
- Add tests in `tests/test_egraph.py`
- Add performance benchmarks

**Success Metrics**:
- Deduplication ratio ≥ 0.9
- 2 new safe rules implemented
- Test coverage ≥ 90%
- Canonicalization performance < 100ms for typical cases""",
        "labels": ["v0.1.1", "egraph", "rules", "testing"],
    },
    {
        "title": "v0.1.1: Budgets/timeout tuning",
        "body": """## Budgets/timeout tuning

**Objective**: Calibrer DomainSpec (OPA verify_ms, budget time_ms) pour p95 audit_cost ≤ baseline −15%

**Acceptance Criteria**:
- [ ] Calibrate OPA verify_ms timeout
- [ ] Optimize budget time_ms allocation
- [ ] p95 audit_cost ≤ baseline −15%
- [ ] Update DomainSpec with optimal values

**Implementation**:
- Create calibration script for timeouts/budgets
- Run performance tests with different timeout values
- Measure audit_cost p95 across configurations
- Update DomainSpec with optimal settings

**Success Metrics**:
- p95 audit_cost ≤ baseline −15%
- OPA verify_ms optimized
- Budget time_ms calibrated
- DomainSpec updated with optimal values""",
        "labels": ["v0.1.1", "performance", "calibration", "domain-spec"],
    },
]

print("GitHub Issues for v0.1.1 hardening:")
print("=" * 50)
print()

for i, issue in enumerate(issues, 1):
    print(f"{i}. {issue['title']}")
    print(f"   Labels: {', '.join(issue['labels'])}")
    print(f"   Body: {issue['body'][:100]}...")
    print()

print("Commands to create issues:")
print("=" * 30)

for i, issue in enumerate(issues, 1):
    print(
        f"gh issue create --title \"{issue['title']}\" --body \"{issue['body']}\" --label {','.join(issue['labels'])}"
    )

print(f"\nTotal: {len(issues)} issues for v0.1.1 hardening")
