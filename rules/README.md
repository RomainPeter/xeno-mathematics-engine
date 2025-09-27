# Incident → Rule Governance

This directory contains rules generated from incidents discovered during S2 testing.

## Rule Format

Each rule follows this structure:

```json
{
  "id": "k-rule-name",
  "title": "Human-readable title",
  "description": "Detailed description of the rule",
  "category": "security|quality|compliance",
  "severity": "high|medium|low",
  "source_incident": "s2_incident_id",
  "obligations": ["k-obligation-1", "k-obligation-2"],
  "test_cases": [
    {
      "name": "test_case_name",
      "description": "What this test validates",
      "expected": "pass|fail"
    }
  ],
  "implementation": {
    "type": "opa|pytest|static_analysis",
    "file": "path/to/implementation",
    "command": "command to run"
  }
}
```

## Rule Generation Process

1. **Incident Detection**: S2 tasks identify specific failure patterns
2. **Rule Creation**: Generate corresponding rule with test cases
3. **Implementation**: Create OPA policy, pytest test, or static analysis rule
4. **Validation**: Ensure rule catches the incident pattern
5. **Integration**: Add to CI pipeline

## Current Rules

- `k-no-secrets`: No hardcoded secrets allowed
- `k-semver-compliance`: Semantic versioning required
- `k-api-versioning`: API changes must be versioned
- `k-deterministic-tests`: Tests must be deterministic
- `k-thread-safe`: Code must be thread-safe
- `k-no-path-traversal`: Path traversal must be blocked
- `k-no-vulnerable-deps`: No vulnerable dependencies
