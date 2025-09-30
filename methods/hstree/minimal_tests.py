"""
HS-Tree Minimal Test Generation
Generates minimal test cases for constraint breach incidents
"""

import json
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestCase:
    """Represents a minimal test case."""

    id: str
    description: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    constraints: List[str]
    priority: int = 1
    category: str = "minimal"


class HSTreeMinimalTests:
    """HS-Tree algorithm for generating minimal test cases."""

    def __init__(self):
        self.test_cases = []
        self.constraint_violations = []
        self.knowledge_base = {}

    def add_constraint_violation(self, violation: Dict[str, Any]):
        """Add a constraint violation to the knowledge base."""
        self.constraint_violations.append(violation)

        # Extract key information
        violation_id = violation.get("id", f"violation_{len(self.constraint_violations)}")
        constraint_type = violation.get("constraint_type", "unknown")
        context = violation.get("context", {})

        # Store in knowledge base
        self.knowledge_base[violation_id] = {
            "constraint_type": constraint_type,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "severity": violation.get("severity", "medium"),
        }

    def generate_minimal_tests(self, constraint_breach: Dict[str, Any]) -> List[TestCase]:
        """Generate minimal test cases for a constraint breach."""
        print(
            f"🔍 Generating minimal tests for constraint breach: {constraint_breach.get('id', 'unknown')}"
        )

        # Extract breach information
        breach_id = constraint_breach.get("id", f"breach_{len(self.constraint_violations)}")
        constraint_type = constraint_breach.get("constraint_type", "unknown")
        context = constraint_breach.get("context", {})

        # Generate test cases based on constraint type
        test_cases = []

        if constraint_type == "semver_violation":
            test_cases.extend(self._generate_semver_tests(breach_id, context))
        elif constraint_type == "license_violation":
            test_cases.extend(self._generate_license_tests(breach_id, context))
        elif constraint_type == "security_violation":
            test_cases.extend(self._generate_security_tests(breach_id, context))
        elif constraint_type == "pii_violation":
            test_cases.extend(self._generate_pii_tests(breach_id, context))
        else:
            test_cases.extend(self._generate_generic_tests(breach_id, context))

        # Add to knowledge base
        self.test_cases.extend(test_cases)

        print(f"✅ Generated {len(test_cases)} minimal test cases")
        return test_cases

    def _generate_semver_tests(self, breach_id: str, context: Dict[str, Any]) -> List[TestCase]:
        """Generate minimal tests for semver violations."""
        tests = []

        # Test 1: Version downgrade
        tests.append(
            TestCase(
                id=f"{breach_id}_semver_downgrade",
                description="Test semver downgrade detection",
                input_data={
                    "current_version": "2.1.0",
                    "new_version": "1.9.0",
                    "package": context.get("package", "test-package"),
                },
                expected_output={"violation": True, "reason": "version_downgrade"},
                constraints=["semver_no_downgrade"],
                priority=1,
                category="semver",
            )
        )

        # Test 2: Invalid version format
        tests.append(
            TestCase(
                id=f"{breach_id}_semver_format",
                description="Test semver format validation",
                input_data={
                    "version": "invalid.version",
                    "package": context.get("package", "test-package"),
                },
                expected_output={"violation": True, "reason": "invalid_format"},
                constraints=["semver_valid_format"],
                priority=2,
                category="semver",
            )
        )

        return tests

    def _generate_license_tests(self, breach_id: str, context: Dict[str, Any]) -> List[TestCase]:
        """Generate minimal tests for license violations."""
        tests = []

        # Test 1: Incompatible license
        tests.append(
            TestCase(
                id=f"{breach_id}_license_incompatible",
                description="Test incompatible license detection",
                input_data={
                    "license": "AGPL-3.0",
                    "project_license": "MIT",
                    "package": context.get("package", "test-package"),
                },
                expected_output={"violation": True, "reason": "license_incompatible"},
                constraints=["license_compatible"],
                priority=1,
                category="license",
            )
        )

        return tests

    def _generate_security_tests(self, breach_id: str, context: Dict[str, Any]) -> List[TestCase]:
        """Generate minimal tests for security violations."""
        tests = []

        # Test 1: Secret detection
        tests.append(
            TestCase(
                id=f"{breach_id}_secret_detection",
                description="Test secret detection",
                input_data={
                    "content": "password = 'secret123'",
                    "file_path": context.get("file_path", "test.py"),
                },
                expected_output={"violation": True, "reason": "secret_detected"},
                constraints=["no_secrets"],
                priority=1,
                category="security",
            )
        )

        return tests

    def _generate_pii_tests(self, breach_id: str, context: Dict[str, Any]) -> List[TestCase]:
        """Generate minimal tests for PII violations."""
        tests = []

        # Test 1: Email detection
        tests.append(
            TestCase(
                id=f"{breach_id}_pii_email",
                description="Test PII email detection",
                input_data={
                    "content": "user@example.com",
                    "file_path": context.get("file_path", "test.py"),
                },
                expected_output={"violation": True, "reason": "pii_email_detected"},
                constraints=["no_pii"],
                priority=1,
                category="pii",
            )
        )

        return tests

    def _generate_generic_tests(self, breach_id: str, context: Dict[str, Any]) -> List[TestCase]:
        """Generate generic minimal tests."""
        tests = []

        tests.append(
            TestCase(
                id=f"{breach_id}_generic",
                description="Generic constraint violation test",
                input_data=context,
                expected_output={"violation": True, "reason": "constraint_violation"},
                constraints=["generic_constraint"],
                priority=3,
                category="generic",
            )
        )

        return tests

    def get_minimal_test_suite(self) -> Dict[str, Any]:
        """Get the complete minimal test suite."""
        return {
            "version": "v0.1.1",
            "generated_at": datetime.now().isoformat(),
            "total_tests": len(self.test_cases),
            "test_cases": [
                {
                    "id": tc.id,
                    "description": tc.description,
                    "input_data": tc.input_data,
                    "expected_output": tc.expected_output,
                    "constraints": tc.constraints,
                    "priority": tc.priority,
                    "category": tc.category,
                }
                for tc in self.test_cases
            ],
            "constraint_violations": len(self.constraint_violations),
            "knowledge_base_size": len(self.knowledge_base),
        }

    def export_tests(self, output_file: str) -> bool:
        """Export test cases to file."""
        try:
            test_suite = self.get_minimal_test_suite()

            with open(output_file, "w") as f:
                json.dump(test_suite, f, indent=2)

            print(f"✅ Exported {len(self.test_cases)} test cases to {output_file}")
            return True

        except Exception as e:
            print(f"❌ Failed to export tests: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get HS-Tree statistics."""
        categories = {}
        for tc in self.test_cases:
            cat = tc.category
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_tests": len(self.test_cases),
            "categories": categories,
            "constraint_violations": len(self.constraint_violations),
            "knowledge_base_size": len(self.knowledge_base),
            "avg_priority": (
                sum(tc.priority for tc in self.test_cases) / len(self.test_cases)
                if self.test_cases
                else 0
            ),
        }


# Global HS-Tree instance
HSTREE = HSTreeMinimalTests()
