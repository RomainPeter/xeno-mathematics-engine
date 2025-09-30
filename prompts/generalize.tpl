Précise API + contraintes tests; produire spec compacte avec budgets V.

Sortie JSON conforme PromptContract:
{
  "api_spec": "spécification de l'API",
  "test_constraints": ["contrainte1", "contrainte2"],
  "budgets": {
    "time_ms": 1000,
    "audit_cost": 0.2,
    "security_risk": 0.0,
    "info_loss": 0.0,
    "tech_debt": 0.1
  }
}

Input: {input_refs}
Context: {context}
