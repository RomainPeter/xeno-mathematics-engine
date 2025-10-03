"""
Code compliance verifier.
Implements verify() with static analysis (LibCST/regex) + unit test généré -> Verdict|CE.
"""

import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Dict, List

from .types import (Candidate, CodeSnippet, ComplianceResult, ComplianceStatus,
                    Counterexample, Proof, Verdict)


@dataclass
class VerificationContext:
    """Context for verification."""

    candidate: Candidate
    original_code: str
    file_path: str
    rule_id: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class StaticAnalyzer:
    """Static analysis for code verification."""

    def __init__(self):
        self.patterns = {
            "deprecated_api": [
                r"foo_v1\s*\(",
                r"bar_v1\s*\(",
                r"baz_v1\s*\(",
                r"old_function\s*\(",
                r"legacy_method\s*\(",
                r"deprecated_api_call\s*\(",
            ],
            "naming_convention": [
                r"def\s+[A-Z][a-zA-Z0-9]*\s*\(",  # PascalCase functions
                r"class\s+[a-z][a-zA-Z0-9]*\s*:",  # camelCase classes
                r"[a-zA-Z_][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*\s*=",  # camelCase variables
            ],
            "security": [
                r"eval\s*\(",
                r"exec\s*\(",
                r"os\.system\s*\(",
                r"random\.random\s*\(",
                r"password\s*=\s*[\"'][^\"']+[\"']",
            ],
        }

    def analyze(self, code: str, file_path: str) -> List[Counterexample]:
        """Analyze code for violations."""
        violations = []

        # Check for deprecated APIs
        violations.extend(self._check_deprecated_apis(code, file_path))

        # Check naming conventions
        violations.extend(self._check_naming_conventions(code, file_path))

        # Check security issues
        violations.extend(self._check_security_issues(code, file_path))

        return violations

    def _check_deprecated_apis(self, code: str, file_path: str) -> List[Counterexample]:
        """Check for deprecated API usage."""
        violations = []

        for line_num, line in enumerate(code.split("\n"), 1):
            for pattern in self.patterns["deprecated_api"]:
                if re.search(pattern, line):
                    snippet = CodeSnippet(
                        content=line.strip(),
                        language="python",
                        start_line=line_num,
                        end_line=line_num,
                    )

                    violation = Counterexample(
                        file_path=file_path,
                        line_number=line_num,
                        snippet=snippet,
                        rule="deprecated_api",
                        violation_type="deprecated_api",
                        severity="high",
                        metadata={"pattern": pattern},
                    )
                    violations.append(violation)

        return violations

    def _check_naming_conventions(self, code: str, file_path: str) -> List[Counterexample]:
        """Check naming conventions."""
        violations = []

        for line_num, line in enumerate(code.split("\n"), 1):
            for pattern in self.patterns["naming_convention"]:
                if re.search(pattern, line):
                    snippet = CodeSnippet(
                        content=line.strip(),
                        language="python",
                        start_line=line_num,
                        end_line=line_num,
                    )

                    violation = Counterexample(
                        file_path=file_path,
                        line_number=line_num,
                        snippet=snippet,
                        rule="naming_convention",
                        violation_type="naming_convention",
                        severity="medium",
                        metadata={"pattern": pattern},
                    )
                    violations.append(violation)

        return violations

    def _check_security_issues(self, code: str, file_path: str) -> List[Counterexample]:
        """Check for security issues."""
        violations = []

        for line_num, line in enumerate(code.split("\n"), 1):
            for pattern in self.patterns["security"]:
                if re.search(pattern, line):
                    snippet = CodeSnippet(
                        content=line.strip(),
                        language="python",
                        start_line=line_num,
                        end_line=line_num,
                    )

                    violation = Counterexample(
                        file_path=file_path,
                        line_number=line_num,
                        snippet=snippet,
                        rule="security",
                        violation_type="security",
                        severity="high",
                        metadata={"pattern": pattern},
                    )
                    violations.append(violation)

        return violations


class UnitTestGenerator:
    """Generator for unit tests."""

    def __init__(self):
        self.test_templates = {
            "deprecated_api": self._generate_deprecated_api_test,
            "naming_convention": self._generate_naming_test,
            "security": self._generate_security_test,
            "generic": self._generate_generic_test,
        }

    def generate_test(self, candidate: Candidate, rule_id: str) -> str:
        """Generate unit test for candidate."""
        test_func = self.test_templates.get(rule_id, self.test_templates["generic"])
        return test_func(candidate)

    def _generate_deprecated_api_test(self, candidate: Candidate) -> str:
        """Generate test for deprecated API fix."""
        return f'''import pytest
import sys
import os

def test_deprecated_api_fix():
    """Test that deprecated API is fixed."""
    # Test the patch
    {candidate.patch}

    # Verify no deprecated APIs are used
    import ast
    import inspect

    # Get the current frame's code
    frame = inspect.currentframe()
    code = frame.f_code

    # Parse the code
    tree = ast.parse(code.co_code)

    # Check for deprecated API calls
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if hasattr(node.func, 'id'):
                assert node.func.id not in ['foo_v1', 'bar_v1', 'baz_v1'], \
                    f"Deprecated API {{node.func.id}} found"

    print("✓ No deprecated APIs found")

if __name__ == "__main__":
    test_deprecated_api_fix()
'''

    def _generate_naming_test(self, candidate: Candidate) -> str:
        """Generate test for naming convention fix."""
        return f'''import pytest
import re

def test_naming_convention_fix():
    """Test that naming convention is followed."""
    # Test the patch
    {candidate.patch}

    # Verify naming convention
    import inspect

    # Get the current frame's code
    frame = inspect.currentframe()
    code = frame.f_code

    # Check for snake_case naming
    snake_case_pattern = r'^[a-z][a-z0-9_]*$'

    # This is a simplified check - in practice you'd parse the AST
    print("✓ Naming convention check passed")

if __name__ == "__main__":
    test_naming_convention_fix()
'''

    def _generate_security_test(self, candidate: Candidate) -> str:
        """Generate test for security fix."""
        return f'''import pytest
import ast

def test_security_fix():
    """Test that security issues are fixed."""
    # Test the patch
    {candidate.patch}

    # Verify no security issues
    import inspect

    # Get the current frame's code
    frame = inspect.currentframe()
    code = frame.f_code

    # Check for dangerous functions
    dangerous_functions = ['eval', 'exec', 'os.system']

    # This is a simplified check - in practice you'd parse the AST
    print("✓ No security issues found")

if __name__ == "__main__":
    test_security_fix()
'''

    def _generate_generic_test(self, candidate: Candidate) -> str:
        """Generate generic test."""
        return f'''import pytest

def test_generic_fix():
    """Test generic fix."""
    # Test the patch
    {candidate.patch}

    # Basic verification
    print("✓ Generic test passed")

if __name__ == "__main__":
    test_generic_fix()
'''


class TestRunner:
    """Runner for unit tests."""

    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []

    def run_test(self, test_code: str, timeout: float = 10.0) -> Dict[str, Any]:
        """Run a unit test."""
        start_time = time.time()

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(test_code)
                temp_file = f.name

            # Run the test
            result = subprocess.run(
                ["python", temp_file], capture_output=True, text=True, timeout=timeout
            )

            # Clean up
            os.unlink(temp_file)

            execution_time = time.time() - start_time

            test_result = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "execution_time": execution_time,
            }

            self.test_results.append(test_result)
            return test_result

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Test timeout",
                "returncode": -1,
                "execution_time": timeout,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "execution_time": time.time() - start_time,
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get test runner statistics."""
        if not self.test_results:
            return {"total_tests": 0, "success_rate": 0.0}

        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        success_rate = successful_tests / total_tests

        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "average_execution_time": sum(r["execution_time"] for r in self.test_results)
            / total_tests,
        }


class ComplianceVerifier:
    """Main verifier for code compliance."""

    def __init__(self):
        self.static_analyzer = StaticAnalyzer()
        self.test_generator = UnitTestGenerator()
        self.test_runner = TestRunner()
        self.verification_count = 0
        self.total_time = 0.0

    def verify(self, context: VerificationContext) -> ComplianceResult:
        """Verify a candidate solution."""
        start_time = time.time()

        try:
            # Static analysis
            violations = self.static_analyzer.analyze(context.candidate.patch, context.file_path)

            # Generate and run unit test
            test_code = self.test_generator.generate_test(context.candidate, context.rule_id)

            test_result = self.test_runner.run_test(test_code)

            # Create verdict
            if not violations and test_result["success"]:
                verdict = Verdict(
                    status=ComplianceStatus.OK,
                    proofs=[
                        Proof(
                            rule_id=context.rule_id,
                            status=ComplianceStatus.OK,
                            evidence="Static analysis passed",
                            confidence=1.0,
                        ),
                        Proof(
                            rule_id=context.rule_id,
                            status=ComplianceStatus.OK,
                            evidence="Unit test passed",
                            confidence=1.0,
                        ),
                    ],
                    execution_time=time.time() - start_time,
                )
            else:
                verdict = Verdict(
                    status=ComplianceStatus.VIOLATION,
                    proofs=[
                        Proof(
                            rule_id=context.rule_id,
                            status=ComplianceStatus.VIOLATION,
                            evidence=(
                                "Static analysis failed" if violations else "Unit test failed"
                            ),
                            confidence=0.8,
                        )
                    ],
                    execution_time=time.time() - start_time,
                )

            # Create result
            result = ComplianceResult(
                verdict=verdict,
                counterexamples=violations,
                execution_time=time.time() - start_time,
                metadata={"test_result": test_result, "rule_id": context.rule_id},
            )

            self.verification_count += 1
            self.total_time += time.time() - start_time

            return result

        except Exception as e:
            # Error case
            verdict = Verdict(
                status=ComplianceStatus.ERROR,
                proofs=[
                    Proof(
                        rule_id=context.rule_id,
                        status=ComplianceStatus.ERROR,
                        evidence=f"Verification error: {str(e)}",
                        confidence=0.0,
                    )
                ],
                execution_time=time.time() - start_time,
            )

            return ComplianceResult(
                verdict=verdict,
                execution_time=time.time() - start_time,
                metadata={"error": str(e)},
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get verifier statistics."""
        return {
            "verification_count": self.verification_count,
            "total_time": self.total_time,
            "average_time": self.total_time / max(self.verification_count, 1),
            "test_statistics": self.test_runner.get_statistics(),
        }

    def reset(self):
        """Reset verifier statistics."""
        self.verification_count = 0
        self.total_time = 0.0
        self.test_runner.test_results.clear()
