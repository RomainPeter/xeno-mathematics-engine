"""
Guard before strategy for policy.secret and policy.egress failures.

Implements enhanced security guards with no-net and no-secrets policies
to prevent data exfiltration and secret exposure.
"""

from typing import Dict, List, Any
from proofengine.orchestrator.strategy_api import (
    Strategy,
    RewritePlan,
    RewriteOperation,
    Guards,
    StrategyContext,
)


class GuardBeforeStrategy(Strategy):
    """Strategy for implementing security guards before operations."""

    def __init__(self):
        """Initialize the guard before strategy."""
        super().__init__(
            id="guard_before",
            trigger_codes=["policy.secret", "policy.egress"],
            expected_outcomes=["policy_clean", "security_improved", "must_block"],
        )
        self.guards = Guards(
            max_depth=2,
            max_rewrites_per_fr=1,
            stop_if_plan_grows=True,
            max_plan_size_increase=4,
        )

    def can_apply(self, context: StrategyContext) -> bool:
        """Check if strategy can be applied to context."""
        # Check if this is a security policy failure
        if not context.failreason.startswith("policy."):
            return False

        # Check if plan has operations that need guarding
        if not self._has_operations_needing_guards(context.plan):
            return False

        # Check depth limit
        if context.depth >= self.guards.max_depth:
            return False

        return True

    def create_rewrite_plan(self, context: StrategyContext) -> RewritePlan:
        """Create rewrite plan for adding security guards."""

        # Analyze current operations
        operations = self._extract_operations(context.plan)
        guard_requirements = self._identify_guard_requirements(
            operations, context.failreason
        )

        if not guard_requirements:
            raise ValueError("No operations found that need security guards")

        # Create guard steps
        steps = []

        # Step 1: Add network isolation guard
        if "egress" in context.failreason or "network" in context.failreason:
            network_guard = {
                "id": "network_isolation_guard",
                "operator": "NetworkGuard",
                "params": {
                    "policy": "no-net",
                    "allowed_domains": [],
                    "block_external": True,
                    "timeout_ms": 5000,
                },
            }
            steps.append(network_guard)

        # Step 2: Add secrets detection guard
        if "secret" in context.failreason:
            secrets_guard = {
                "id": "secrets_detection_guard",
                "operator": "SecretsGuard",
                "params": {
                    "policy": "no-secrets",
                    "scan_patterns": [
                        r"password\s*=\s*['\"][^'\"]+['\"]",
                        r"api_key\s*=\s*['\"][^'\"]+['\"]",
                        r"secret\s*=\s*['\"][^'\"]+['\"]",
                        r"token\s*=\s*['\"][^'\"]+['\"]",
                    ],
                    "block_on_match": True,
                    "scan_files": True,
                    "scan_env": True,
                },
            }
            steps.append(secrets_guard)

        # Step 3: Add execution sandbox guard
        sandbox_guard = {
            "id": "execution_sandbox_guard",
            "operator": "SandboxGuard",
            "params": {
                "policy": "restricted",
                "allowed_operations": ["read", "compute"],
                "blocked_operations": ["write", "network", "file_system"],
                "timeout_ms": 10000,
                "memory_limit_mb": 512,
            },
        }
        steps.append(sandbox_guard)

        # Step 4: Add audit logging guard
        audit_guard = {
            "id": "audit_logging_guard",
            "operator": "AuditGuard",
            "params": {
                "log_level": "security",
                "log_operations": True,
                "log_data_access": True,
                "log_network_calls": True,
                "retention_days": 30,
            },
        }
        steps.append(audit_guard)

        return RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:current_step",
            steps=steps,
            params_patch={
                "security_level": "maximum",
                "network_isolation": "enabled",
                "secrets_protection": "enabled",
                "audit_logging": "enabled",
            },
        )

    def estimate_success_probability(self, context: StrategyContext) -> bool:
        """Estimate success probability for guard implementation."""
        base_prob = 0.95  # Very high success rate for guard implementation

        # Adjust based on context
        if context.failreason in ["policy.secret", "policy.egress"]:
            base_prob += 0.03  # Perfect match

        # Check if plan has clear operation structure
        if self._has_clear_operation_structure(context.plan):
            base_prob += 0.02

        # Check for existing security infrastructure
        if self._has_existing_security_infrastructure(context.plan):
            base_prob += 0.02

        return min(base_prob, 1.0)

    def _has_operations_needing_guards(self, plan: Dict[str, Any]) -> bool:
        """Check if plan has operations that need security guards."""
        steps = plan.get("steps", [])

        # Look for operations that might need guarding
        risky_operations = [
            "NetworkCall",
            "FileAccess",
            "DatabaseQuery",
            "ExternalAPI",
            "DataProcessing",
            "CodeExecution",
            "SystemCommand",
        ]

        for step in steps:
            operator = step.get("operator", "")
            if any(risky_op in operator for risky_op in risky_operations):
                return True

        return False

    def _extract_operations(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract operations from plan that might need guarding."""
        steps = plan.get("steps", [])
        operations = []

        for step in steps:
            operator = step.get("operator", "")
            if self._is_risky_operation(operator):
                operations.append(
                    {
                        "id": step.get("id"),
                        "operator": operator,
                        "params": step.get("params", {}),
                        "risk_level": self._assess_operation_risk(
                            operator, step.get("params", {})
                        ),
                    }
                )

        return operations

    def _is_risky_operation(self, operator: str) -> bool:
        """Check if operation is risky and needs guarding."""
        risky_operators = [
            "NetworkCall",
            "FileAccess",
            "DatabaseQuery",
            "ExternalAPI",
            "DataProcessing",
            "CodeExecution",
            "SystemCommand",
            "DataExport",
            "NetworkRequest",
            "FileWrite",
            "DatabaseUpdate",
        ]

        return any(risky_op in operator for risky_op in risky_operators)

    def _assess_operation_risk(self, operator: str, params: Dict[str, Any]) -> str:
        """Assess risk level of operation."""
        if "Network" in operator or "External" in operator:
            return "high"
        elif "Database" in operator or "File" in operator:
            return "medium"
        else:
            return "low"

    def _identify_guard_requirements(
        self, operations: List[Dict[str, Any]], failreason: str
    ) -> List[str]:
        """Identify what guards are needed based on operations and failure reason."""
        requirements = []

        # Network-related guards
        if any(
            "Network" in op["operator"] or "External" in op["operator"]
            for op in operations
        ):
            requirements.append("network_isolation")

        # Secrets-related guards
        if "secret" in failreason or any(
            "secret" in str(op["params"]).lower() for op in operations
        ):
            requirements.append("secrets_detection")

        # Data access guards
        if any(
            "Database" in op["operator"] or "File" in op["operator"]
            for op in operations
        ):
            requirements.append("data_access_control")

        # Always add audit logging
        requirements.append("audit_logging")

        return requirements

    def _has_clear_operation_structure(self, plan: Dict[str, Any]) -> bool:
        """Check if plan has clear operation structure."""
        steps = plan.get("steps", [])
        return len(steps) > 0 and all(
            step.get("id") and step.get("operator") for step in steps
        )

    def _has_existing_security_infrastructure(self, plan: Dict[str, Any]) -> bool:
        """Check if plan already has security infrastructure."""
        steps = plan.get("steps", [])
        security_steps = [
            s
            for s in steps
            if s.get("operator")
            in ["SecurityGuard", "NetworkGuard", "SecretsGuard", "AuditGuard"]
        ]
        return len(security_steps) > 0
