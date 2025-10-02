"""
FailReason v0.2 mapping for different runners.
Maps runner types to granular failreason codes.
"""

from enum import Enum
from typing import Any, Dict, List


class RunnerType(Enum):
    """Types of runners in the system."""

    PYTEST = "pytest"
    OPA = "opa"
    STATIC = "static"
    VERIFIER = "verifier"


class FailReasonMapper:
    """Maps runner outputs to granular FailReason codes."""

    def __init__(self):
        self._mappings = {
            RunnerType.PYTEST: {
                "test_failure": "runner.pytest_failure",
                "timeout": "runner.verifier_timeout",
                "flaky": "nondet.flaky_test",
                "race_condition": "nondet.race_condition",
                "seed_dependent": "nondet.seed_dependent",
                "missing_test": "coverage.missing_tests",
                "insufficient_coverage": "coverage.insufficient_line_coverage",
            },
            RunnerType.OPA: {
                "policy_violation": "runner.opa_policy_violation",
                "semver_violation": "policy.semver_violation",
                "changelog_missing": "policy.changelog_missing",
                "secret_detection": "policy.secret_detection",
                "breaking_change": "policy.breaking_change",
            },
            RunnerType.STATIC: {
                "analysis_failure": "runner.static_analysis_failure",
                "type_error": "schema.invalid_type",
                "missing_field": "schema.missing_required_field",
                "constraint_violation": "schema.constraint_violation",
            },
            RunnerType.VERIFIER: {
                "verification_timeout": "runner.verifier_timeout",
                "budget_exceeded": "budget.time_exceeded",
                "audit_cost_exceeded": "budget.audit_cost_exceeded",
                "max_replans_exceeded": "budget.max_replans_exceeded",
            },
        }

        self._severity_mapping = {
            "runner.pytest_failure": "medium",
            "runner.opa_policy_violation": "high",
            "runner.static_analysis_failure": "medium",
            "runner.verifier_timeout": "low",
            "policy.semver_violation": "high",
            "policy.changelog_missing": "medium",
            "policy.secret_detection": "critical",
            "policy.breaking_change": "high",
            "budget.time_exceeded": "low",
            "budget.audit_cost_exceeded": "medium",
            "budget.max_replans_exceeded": "low",
            "contract.ambiguous_spec": "medium",
            "contract.missing_obligation": "high",
            "contract.insufficient_coverage": "medium",
            "coverage.missing_tests": "medium",
            "coverage.insufficient_line_coverage": "low",
            "nondet.flaky_test": "low",
            "nondet.race_condition": "medium",
            "nondet.seed_dependent": "low",
            "api.semver_missing": "high",
            "api.changelog_missing": "medium",
            "api.breaking_change": "high",
        }

    def map_runner_output(
        self, runner_type: RunnerType, error_type: str, error_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map runner output to FailReason v0.2 format."""

        # Get the mapped code
        mapped_code = self._mappings.get(runner_type, {}).get(error_type)
        if not mapped_code:
            # Fallback to generic error
            mapped_code = f"{runner_type.value}.{error_type}"

        # Get severity
        severity = self._severity_mapping.get(mapped_code, "medium")

        # Extract tags based on error type and data
        tags = self._extract_tags(runner_type, error_type, error_data)

        return {
            "version": "0.2.0",
            "code": mapped_code,
            "message": error_data.get("message", f"{error_type} from {runner_type.value}"),
            "refs": error_data.get("refs", []),
            "data": error_data.get("data", {}),
            "runner": runner_type.value,
            "severity": severity,
            "tags": tags,
        }

    def _extract_tags(
        self, runner_type: RunnerType, error_type: str, error_data: Dict[str, Any]
    ) -> List[str]:
        """Extract relevant tags from error data."""
        tags = []

        # Add runner-specific tags
        if runner_type == RunnerType.PYTEST:
            tags.extend(["test", "execution"])
        elif runner_type == RunnerType.OPA:
            tags.extend(["policy", "compliance"])
        elif runner_type == RunnerType.STATIC:
            tags.extend(["static", "analysis"])
        elif runner_type == RunnerType.VERIFIER:
            tags.extend(["verification", "budget"])

        # Add error-specific tags
        if "api" in error_type:
            tags.append("api")
        if "breaking" in error_type:
            tags.append("breaking_change")
        if "secret" in error_type:
            tags.append("security")
        if "flaky" in error_type or "nondet" in error_type:
            tags.append("nondeterministic")
        if "coverage" in error_type:
            tags.append("coverage")
        if "budget" in error_type:
            tags.append("budget")

        # Add tags from error data
        if "tags" in error_data:
            tags.extend(error_data["tags"])

        return list(set(tags))  # Remove duplicates

    def get_strategies_for_failreason(self, failreason_code: str) -> List[str]:
        """Get recommended strategies for a specific failreason."""
        strategy_mapping = {
            "contract.ambiguous_spec": ["specialize_then_retry"],
            "coverage.missing_tests": ["add_missing_tests"],
            "api.semver_missing": ["require_semver"],
            "api.changelog_missing": ["changelog_or_block"],
            "runner.test_failure": ["decompose_meet"],
            "nondet.flaky_test": ["retry_with_hardening"],
            "api.breaking_change": ["rollback_and_patch"],
            "policy.secret_detection": ["require_semver"],  # Fallback strategy
        }

        return strategy_mapping.get(failreason_code, [])

    def get_failreason_hierarchy(self) -> Dict[str, List[str]]:
        """Get the hierarchical structure of failreason codes."""
        return {
            "parse": [
                "parse.json_syntax_error",
                "parse.yaml_syntax_error",
                "parse.schema_validation_error",
            ],
            "schema": [
                "schema.missing_required_field",
                "schema.invalid_type",
                "schema.constraint_violation",
            ],
            "runner": [
                "runner.pytest_failure",
                "runner.opa_policy_violation",
                "runner.static_analysis_failure",
                "runner.verifier_timeout",
            ],
            "policy": [
                "policy.semver_violation",
                "policy.changelog_missing",
                "policy.secret_detection",
                "policy.breaking_change",
            ],
            "budget": [
                "budget.time_exceeded",
                "budget.audit_cost_exceeded",
                "budget.max_replans_exceeded",
            ],
            "contract": [
                "contract.ambiguous_spec",
                "contract.missing_obligation",
                "contract.insufficient_coverage",
            ],
            "coverage": [
                "coverage.missing_tests",
                "coverage.insufficient_branch_coverage",
                "coverage.insufficient_line_coverage",
            ],
            "nondet": [
                "nondet.flaky_test",
                "nondet.race_condition",
                "nondet.seed_dependent",
            ],
            "api": [
                "api.semver_missing",
                "api.changelog_missing",
                "api.breaking_change",
            ],
        }
