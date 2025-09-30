"""
FailReason v1 handlers for Discovery Engine 2-Cat.
Maps incidents to rules and triggers replanning.
"""

from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from methods.hstree.minimal_tests import HSTreeMinimalTests


class FailReasonCategory(Enum):
    """Categories of failure reasons."""

    VALIDATION = "validation"
    RUNTIME = "runtime"
    POLICY = "policy"
    RESOURCE = "resource"
    DIVERSITY = "diversity"
    NOVELTY = "novelty"
    COVERAGE = "coverage"


@dataclass
class FailReason:
    """Represents a failure reason with handler action."""

    code: str
    message: str
    category: FailReasonCategory
    details: Dict[str, Any]
    handler_action: str


class IncidentHandler:
    """Handles incidents and transforms them into rules."""

    def __init__(self):
        self.incident_history = []
        self.rule_generations = []
        self.handler_mappings = self._initialize_handler_mappings()
        self.hstree = HSTreeMinimalTests()

    def _initialize_handler_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize default handler mappings."""
        return {
            "LowNovelty": {
                "handler": "egraph_add_equiv_forbidden",
                "action": "add_equiv_forbidden(imp_variant)",
                "description": "Add forbidden equivalence for low novelty implication variant",
            },
            "LowCoverage": {
                "handler": "add_target_in_K",
                "action": "prioritize Meet/Generalize in policy",
                "description": "Add target to K and prioritize Meet/Generalize operations",
            },
            "ConstraintBreach": {
                "handler": "add_opa_rule_and_test",
                "action": "add OPA rule + test; block faulty path in e-graph",
                "description": "Add OPA rule and test, block faulty path in e-graph",
            },
            "OracleTimeout": {
                "handler": "increase_budget_or_quarantine",
                "action": "increase budget/timeout or quarantine seeds",
                "description": "Increase budget/timeout or quarantine problematic seeds",
            },
            "Flaky": {
                "handler": "quarantine_seeds",
                "action": "quarantine seeds and increase robustness",
                "description": "Quarantine flaky seeds and increase system robustness",
            },
        }

    def handle_incident(
        self, incident: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle an incident and generate appropriate rules."""
        print(f"🔧 Handling incident: {incident.get('type', 'unknown')}")

        # Extract failure reason
        fail_reason = self._extract_fail_reason(incident)

        # Determine handler action
        handler_result = self._determine_handler_action(fail_reason, incident, state)

        # Generate rule from incident
        rule = self._generate_rule_from_incident(incident, fail_reason, handler_result)

        # Update state with new rule
        updated_state = self._update_state_with_rule(state, rule)

        # Record incident handling
        self._record_incident_handling(incident, fail_reason, handler_result, rule)

        return {
            "updated_state": updated_state,
            "generated_rule": rule,
            "handler_result": handler_result,
            "replanning_required": self._should_replan(fail_reason, handler_result),
        }

    def _extract_fail_reason(self, incident: Dict[str, Any]) -> FailReason:
        """Extract failure reason from incident."""
        incident_type = incident.get("type", "unknown")
        details = incident.get("details", {})

        # Map incident types to failure reasons
        if "low_novelty" in incident_type.lower():
            return FailReason(
                code="LowNovelty",
                message="Implication has low novelty score",
                category=FailReasonCategory.NOVELTY,
                details=details,
                handler_action="egraph_add_equiv_forbidden",
            )
        elif "low_coverage" in incident_type.lower():
            return FailReason(
                code="LowCoverage",
                message="Implication has low coverage gain",
                category=FailReasonCategory.COVERAGE,
                details=details,
                handler_action="add_target_in_K",
            )
        elif "constraint" in incident_type.lower():
            return FailReason(
                code="ConstraintBreach",
                message="Policy constraint violated",
                category=FailReasonCategory.POLICY,
                details=details,
                handler_action="add_opa_rule_and_test",
            )
        elif "timeout" in incident_type.lower():
            return FailReason(
                code="OracleTimeout",
                message="Oracle verification timeout",
                category=FailReasonCategory.RESOURCE,
                details=details,
                handler_action="increase_budget_or_quarantine",
            )
        elif "flaky" in incident_type.lower():
            return FailReason(
                code="Flaky",
                message="Flaky or unreliable behavior detected",
                category=FailReasonCategory.RUNTIME,
                details=details,
                handler_action="quarantine_seeds",
            )
        else:
            return FailReason(
                code="Unknown",
                message="Unknown failure reason",
                category=FailReasonCategory.RUNTIME,
                details=details,
                handler_action="generic_handler",
            )

    def _determine_handler_action(
        self, fail_reason: FailReason, incident: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine appropriate handler action."""
        # handler_mapping = self.handler_mappings.get(fail_reason.code, {})  # Not used in this implementation

        if fail_reason.code == "LowNovelty":
            return self._handle_low_novelty(incident, state)
        elif fail_reason.code == "LowCoverage":
            return self._handle_low_coverage(incident, state)
        elif fail_reason.code == "ConstraintBreach":
            return self._handle_constraint_breach(incident, state)
        elif fail_reason.code == "OracleTimeout":
            return self._handle_oracle_timeout(incident, state)
        elif fail_reason.code == "Flaky":
            return self._handle_flaky(incident, state)
        else:
            return self._handle_generic(incident, state)

    def _handle_low_novelty(
        self, incident: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle low novelty incident."""
        print("🔧 Handling LowNovelty: Adding forbidden equivalence")

        # Extract implication variant
        implication = incident.get("implication", {})
        variant = implication.get("variant", implication)

        # Add forbidden equivalence to e-graph
        forbidden_equiv = {
            "type": "forbidden_equivalence",
            "implication_id": implication.get("id"),
            "variant": variant,
            "reason": "low_novelty",
            "timestamp": datetime.now().isoformat(),
        }

        return {
            "action": "egraph_add_equiv_forbidden",
            "forbidden_equivalence": forbidden_equiv,
            "description": "Added forbidden equivalence for low novelty variant",
        }

    def _handle_low_coverage(
        self, incident: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle low coverage incident."""
        print(
            "🔧 Handling LowCoverage: Adding target to K and prioritizing Meet/Generalize"
        )

        # Add target to K
        target = {
            "type": "coverage_target",
            "implication_id": incident.get("implication", {}).get("id"),
            "coverage_gap": incident.get("details", {}).get("coverage_gap", 0.1),
            "timestamp": datetime.now().isoformat(),
        }

        # Prioritize Meet/Generalize operations
        policy_update = {
            "type": "policy_update",
            "action": "prioritize_meet_generalize",
            "operations": ["Meet", "Generalize"],
            "priority_boost": 0.2,
            "timestamp": datetime.now().isoformat(),
        }

        return {
            "action": "add_target_in_K",
            "target": target,
            "policy_update": policy_update,
            "description": "Added coverage target and prioritized Meet/Generalize",
        }

    def _handle_constraint_breach(
        self, incident: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle constraint breach incident with HS-Tree minimal test generation."""
        print("🔧 Handling ConstraintBreach: Adding OPA rule and HS-Tree minimal tests")

        # Extract constraint details
        constraint = incident.get("constraint", {})
        violation = incident.get("violation", {})

        # Add constraint violation to HS-Tree
        self.hstree.add_constraint_violation(
            {
                "id": incident.get("id", "unknown"),
                "constraint_type": constraint.get("type", "unknown"),
                "context": violation.get("context", {}),
                "severity": incident.get("severity", "medium"),
            }
        )

        # Generate minimal tests using HS-Tree
        minimal_tests = self.hstree.generate_minimal_tests(incident)

        # Generate OPA rule
        opa_rule = {
            "type": "opa_rule",
            "name": f"constraint_{constraint.get('id', 'unknown')}",
            "content": f"deny[msg] {{ {constraint.get('condition', 'true')}; msg := \"{constraint.get('message', 'Constraint violated')}\" }}",
            "source": "incident_handler",
            "timestamp": datetime.now().isoformat(),
        }

        # Generate test from HS-Tree
        test = {
            "type": "test",
            "name": f"test_constraint_{constraint.get('id', 'unknown')}",
            "input": violation.get("input", {}),
            "expected_deny": True,
            "source": "incident_handler",
            "minimal_tests": [
                {
                    "id": tc.id,
                    "description": tc.description,
                    "input_data": tc.input_data,
                    "expected_output": tc.expected_output,
                    "constraints": tc.constraints,
                    "priority": tc.priority,
                    "category": tc.category,
                }
                for tc in minimal_tests
            ],
            "timestamp": datetime.now().isoformat(),
        }

        # Block faulty path in e-graph
        blocked_path = {
            "type": "blocked_path",
            "path": violation.get("path", []),
            "reason": "constraint_breach",
            "timestamp": datetime.now().isoformat(),
        }

        # Add minimal tests to knowledge base
        for tc in minimal_tests:
            if "K" not in state:
                state["K"] = {}
            state["K"][f"minimal_test_{tc.id}"] = {
                "type": "minimal_test",
                "id": tc.id,
                "description": tc.description,
                "input_data": tc.input_data,
                "expected_output": tc.expected_output,
                "constraints": tc.constraints,
                "priority": tc.priority,
                "category": tc.category,
                "source": "hstree",
                "timestamp": datetime.now().isoformat(),
            }

        return {
            "action": "add_opa_rule_and_test",
            "opa_rule": opa_rule,
            "test": test,
            "blocked_path": blocked_path,
            "minimal_tests": len(minimal_tests),
            "hstree_stats": self.hstree.get_stats(),
            "description": f"Added OPA rule, test, {len(minimal_tests)} minimal tests, and blocked faulty path",
        }

    def _handle_oracle_timeout(
        self, incident: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle oracle timeout incident."""
        print("🔧 Handling OracleTimeout: Increasing budget/timeout")

        current_timeout = incident.get("timeout_ms", 8000)
        new_timeout = int(current_timeout * 1.5)  # Increase by 50%

        # Update timeout
        timeout_update = {
            "type": "timeout_update",
            "old_timeout_ms": current_timeout,
            "new_timeout_ms": new_timeout,
            "reason": "oracle_timeout",
            "timestamp": datetime.now().isoformat(),
        }

        # Quarantine problematic seeds if timeout persists
        quarantine = {
            "type": "quarantine",
            "seeds": incident.get("problematic_seeds", []),
            "reason": "oracle_timeout",
            "timestamp": datetime.now().isoformat(),
        }

        return {
            "action": "increase_budget_or_quarantine",
            "timeout_update": timeout_update,
            "quarantine": quarantine,
            "description": f"Increased timeout to {new_timeout}ms and quarantined seeds",
        }

    def _handle_flaky(
        self, incident: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle flaky behavior incident."""
        print("🔧 Handling Flaky: Quarantining seeds and increasing robustness")

        # Quarantine flaky seeds
        flaky_seeds = incident.get("flaky_seeds", [])
        quarantine = {
            "type": "quarantine",
            "seeds": flaky_seeds,
            "reason": "flaky_behavior",
            "timestamp": datetime.now().isoformat(),
        }

        # Increase robustness
        robustness_update = {
            "type": "robustness_update",
            "retry_count": incident.get("retry_count", 1) + 1,
            "confidence_threshold": 0.8,  # Higher confidence required
            "timestamp": datetime.now().isoformat(),
        }

        return {
            "action": "quarantine_seeds",
            "quarantine": quarantine,
            "robustness_update": robustness_update,
            "description": "Quarantined flaky seeds and increased robustness",
        }

    def _handle_generic(
        self, incident: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle generic incident."""
        print("🔧 Handling Generic incident")

        return {
            "action": "generic_handler",
            "description": "Applied generic incident handling",
            "timestamp": datetime.now().isoformat(),
        }

    def _generate_rule_from_incident(
        self,
        incident: Dict[str, Any],
        fail_reason: FailReason,
        handler_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate rule from incident."""
        rule = {
            "id": f"rule_{len(self.rule_generations) + 1}_{int(datetime.now().timestamp())}",
            "type": "incident_generated_rule",
            "incident_id": incident.get("id", "unknown"),
            "fail_reason": fail_reason.code,
            "handler_action": handler_result.get("action"),
            "content": f"Rule generated from {fail_reason.code} incident",
            "details": {
                "incident": incident,
                "fail_reason": {
                    "code": fail_reason.code,
                    "message": fail_reason.message,
                    "category": fail_reason.category.value,
                },
                "handler_result": handler_result,
            },
            "timestamp": datetime.now().isoformat(),
        }

        return rule

    def _update_state_with_rule(
        self, state: Dict[str, Any], rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update state with generated rule."""
        updated_state = state.copy()

        # Add rule to K (Knowledge)
        if "K" not in updated_state:
            updated_state["K"] = {}

        updated_state["K"][rule["id"]] = rule

        # Update other state components based on rule type
        if rule.get("handler_action") == "egraph_add_equiv_forbidden":
            # Add to e-graph forbidden equivalences
            if "forbidden_equivalences" not in updated_state:
                updated_state["forbidden_equivalences"] = []
            updated_state["forbidden_equivalences"].append(
                rule["details"]["handler_result"]["forbidden_equivalence"]
            )

        elif rule.get("handler_action") == "add_target_in_K":
            # Add coverage targets
            if "coverage_targets" not in updated_state:
                updated_state["coverage_targets"] = []
            updated_state["coverage_targets"].append(
                rule["details"]["handler_result"]["target"]
            )

        return updated_state

    def _should_replan(
        self, fail_reason: FailReason, handler_result: Dict[str, Any]
    ) -> bool:
        """Determine if replanning is required."""
        # Replan for significant changes
        replan_triggers = [
            "add_target_in_K",
            "add_opa_rule_and_test",
            "increase_budget_or_quarantine",
        ]

        return handler_result.get("action") in replan_triggers

    def _record_incident_handling(
        self,
        incident: Dict[str, Any],
        fail_reason: FailReason,
        handler_result: Dict[str, Any],
        rule: Dict[str, Any],
    ):
        """Record incident handling for audit."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "incident": incident,
            "fail_reason": {
                "code": fail_reason.code,
                "message": fail_reason.message,
                "category": fail_reason.category.value,
            },
            "handler_result": handler_result,
            "generated_rule": rule,
            "replanning_required": self._should_replan(fail_reason, handler_result),
        }

        self.incident_history.append(record)
        self.rule_generations.append(rule)

    def get_incident_stats(self) -> Dict[str, Any]:
        """Get incident handling statistics."""
        if not self.incident_history:
            return {"total_incidents": 0, "total_rules_generated": 0}

        # Count by failure reason
        fail_reason_counts = {}
        for record in self.incident_history:
            code = record["fail_reason"]["code"]
            fail_reason_counts[code] = fail_reason_counts.get(code, 0) + 1

        return {
            "total_incidents": len(self.incident_history),
            "total_rules_generated": len(self.rule_generations),
            "fail_reason_counts": fail_reason_counts,
            "replanning_required_count": sum(
                1 for r in self.incident_history if r["replanning_required"]
            ),
        }


# Global incident handler instance
incident_handler = IncidentHandler()
