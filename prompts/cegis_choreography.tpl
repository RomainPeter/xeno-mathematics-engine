You are an expert in program synthesis and choreography design. Your task is to generate variant choreographies (sequences of operations) for the CEGIS (Counter-Example Guided Inductive Synthesis) process.

## Context
- Domain: {{domain}}
- Target goal: {{goal}}
- Constraints K: {{constraints}}
- Budget V: {{budget}}
- Failed choreography: {{failed_choreography}}
- Counterexample: {{counterexample}}

## Available Operations
- Meet (∧): Combine constraints/evidence
- Generalize (↑): Generalize patterns
- Specialize (↓): Specialize for specific cases
- Contrast (Δ): Find differences
- Refute (⊥): Refute invalid claims
- Normalize (□): Canonicalize representations
- Verify (№): Verify properties
- Abduce (⟂): Generate hypotheses

## Task
Generate 3-5 variant choreographies that:
1. Address the failure in the previous choreography
2. Respect the constraints K
3. Stay within budget V
4. Maximize expected gains (coverage, MDL, novelty)
5. Are syntactically valid sequences

## Output Format
Return a JSON array of choreographies:
```json
[
  {
    "id": "choreo_<timestamp>",
    "ops": ["Meet", "Verify", "Normalize"],
    "pre": {"constraints": ["K1", "K2"]},
    "post": {"expected_gains": {"coverage": 0.8, "MDL": -0.3}},
    "guards": ["K1", "K2"],
    "budgets": {"time_ms": 1000, "audit_cost": 50},
    "diversity_keys": ["constraint_focus", "verification_heavy"],
    "rationale": "Explanation of why this choreography should work"
  }
]
```

## Examples for RegTech/Code domain:
- ["Meet", "Verify", "Normalize"] - Basic constraint checking
- ["Generalize", "Contrast", "Verify"] - Pattern analysis
- ["Abduce", "Specialize", "Verify"] - Hypothesis-driven approach

Generate choreographies now:
