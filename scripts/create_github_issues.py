#!/usr/bin/env python3
"""
Create GitHub Issues for Top-Lab Readiness Epic
"""

issues = [
    {
        "title": "Nightly Bench + badge + job summary",
        "body": "Implement nightly benchmark workflow with job summary and artifacts",
        "labels": ["epic", "bench"],
    },
    {
        "title": "Release guardrails: SBOM High=0, cosign attest required",
        "body": "Enforce release guardrails with SBOM High=0, cosign attest required",
        "labels": ["epic", "ops"],
    },
    {
        "title": "Metrics rollup + δ–incidents correlation",
        "body": "Implement metrics rollup with δ-incidents correlation analysis",
        "labels": ["epic", "bench"],
    },
    {
        "title": "HS-Tree diagnostics MVP",
        "body": "Implement HS-Tree diagnostics for minimal test generation (RegTech/Code)",
        "labels": ["epic"],
    },
    {
        "title": "IDS sampler MVP + policy integration",
        "body": "Implement IDS sampler for information-directed exploration",
        "labels": ["epic"],
    },
    {
        "title": "CVaR in V + selection policy integration",
        "body": "Integrate CVaR in cost vector V and selection policy",
        "labels": ["epic"],
    },
    {
        "title": "2-morphism strategy layer",
        "body": "Implement 2-morphism strategy layer with fallback taxonomy",
        "labels": ["epic"],
    },
    {
        "title": "Docs: Runbook, Operating Contract, Reproducibility, Bench Pack",
        "body": "Complete documentation suite for production operations",
        "labels": ["epic", "ops"],
    },
    {
        "title": "Grove Pack: one-pager, script, form drafts",
        "body": "Create Grove Pack with one-pager, 90s script, form drafts",
        "labels": ["epic"],
    },
]

print("GitHub Issues to create for Top-Lab Readiness Epic:")
print("=" * 60)

for i, issue in enumerate(issues, 1):
    print(f"\n{i}. {issue['title']}")
    print(f"   Labels: {', '.join(issue['labels'])}")
    print(f"   Body: {issue['body']}")
    print(
        f"   Command: gh issue create --title \"{issue['title']}\" --body \"{issue['body']}\" --label {','.join(issue['labels'])}"
    )

print(f"\nTotal: {len(issues)} issues to create")
print("\nTo create these issues, run the commands above with GitHub CLI (gh)")
