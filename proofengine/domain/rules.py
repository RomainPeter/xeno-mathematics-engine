"""
Code compliance rules implementation.
Provides specific rules for code compliance verification.
"""

import re
from typing import List, Dict, Any, Set
from dataclasses import dataclass

from .types import Counterexample, CodeSnippet


@dataclass
class RulePattern:
    """Pattern for rule matching."""

    regex: str
    flags: int = 0
    description: str = ""

    def match(self, content: str) -> List[re.Match]:
        """Find all matches in content."""
        pattern = re.compile(self.regex, self.flags)
        return list(pattern.finditer(content))


class DeprecatedAPIRule:
    """Rule for detecting deprecated API usage."""

    def __init__(self, deprecated_apis: List[str]):
        self.deprecated_apis = deprecated_apis
        self.rule_id = "deprecated_api"
        self.name = "Deprecated API Usage"
        self.description = "Detects usage of deprecated APIs"
        self.severity = "high"

    def check(self, file_path: str, content: str) -> List[Counterexample]:
        """Check for deprecated API usage."""
        violations = []

        for line_num, line in enumerate(content.split("\n"), 1):
            for api in self.deprecated_apis:
                if api in line:
                    # Find the exact location
                    api_start = line.find(api)
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
                        rule=self.rule_id,
                        violation_type="deprecated_api",
                        severity=self.severity,
                        metadata={"deprecated_api": api, "column": api_start + 1},
                    )
                    violations.append(violation)

        return violations


class NamingConventionRule:
    """Rule for enforcing naming conventions."""

    def __init__(self, convention: str = "snake_case"):
        self.convention = convention
        self.rule_id = "naming_convention"
        self.name = "Naming Convention"
        self.description = f"Enforces {convention} naming convention"
        self.severity = "medium"

        # Define patterns for different conventions
        self.patterns = {
            "snake_case": r"\b[a-z][a-z0-9_]*\b",
            "camelCase": r"\b[a-z][a-zA-Z0-9]*\b",
            "PascalCase": r"\b[A-Z][a-zA-Z0-9]*\b",
        }

    def check(self, file_path: str, content: str) -> List[Counterexample]:
        """Check naming conventions."""
        violations = []

        if self.convention not in self.patterns:
            return violations

        pattern = re.compile(self.patterns[self.convention])

        for line_num, line in enumerate(content.split("\n"), 1):
            # Find function definitions, class definitions, variable assignments
            if (
                re.search(r"\bdef\s+", line)
                or re.search(r"\bclass\s+", line)
                or re.search(r"\b[a-zA-Z_][a-zA-Z0-9_]*\s*=", line)
            ):
                matches = pattern.finditer(line)
                for match in matches:
                    name = match.group()
                    if not self._is_valid_name(name):
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
                            rule=self.rule_id,
                            violation_type="naming_convention",
                            severity=self.severity,
                            metadata={
                                "convention": self.convention,
                                "name": name,
                                "column": match.start() + 1,
                            },
                        )
                        violations.append(violation)

        return violations

    def _is_valid_name(self, name: str) -> bool:
        """Check if name follows the convention."""
        if self.convention == "snake_case":
            return re.match(r"^[a-z][a-z0-9_]*$", name) is not None
        elif self.convention == "camelCase":
            return re.match(r"^[a-z][a-zA-Z0-9]*$", name) is not None
        elif self.convention == "PascalCase":
            return re.match(r"^[A-Z][a-zA-Z0-9]*$", name) is not None
        return True


class SecurityRule:
    """Rule for detecting security vulnerabilities."""

    def __init__(self):
        self.rule_id = "security"
        self.name = "Security Vulnerabilities"
        self.description = "Detects potential security vulnerabilities"
        self.severity = "high"

        # Define security patterns
        self.patterns = {
            "hardcoded_password": r'password\s*=\s*["\'][^"\']+["\']',
            "sql_injection": r'execute\s*\(\s*["\'][^"\']*%[^"\']*["\']',
            "eval_usage": r"\beval\s*\(",
            "exec_usage": r"\bexec\s*\(",
            "shell_injection": r"os\.system\s*\(",
            "unsafe_random": r"random\.random\s*\(",
        }

    def check(self, file_path: str, content: str) -> List[Counterexample]:
        """Check for security vulnerabilities."""
        violations = []

        for pattern_name, pattern in self.patterns.items():
            regex = re.compile(pattern, re.IGNORECASE)

            for line_num, line in enumerate(content.split("\n"), 1):
                matches = regex.finditer(line)
                for match in matches:
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
                        rule=self.rule_id,
                        violation_type="security",
                        severity=self.severity,
                        metadata={"pattern": pattern_name, "column": match.start() + 1},
                    )
                    violations.append(violation)

        return violations


class CodeStyleRule:
    """Rule for enforcing code style."""

    def __init__(self):
        self.rule_id = "code_style"
        self.name = "Code Style"
        self.description = "Enforces code style guidelines"
        self.severity = "low"

    def check(self, file_path: str, content: str) -> List[Counterexample]:
        """Check code style."""
        violations = []

        for line_num, line in enumerate(content.split("\n"), 1):
            # Check for trailing whitespace
            if line.rstrip() != line:
                snippet = CodeSnippet(
                    content=line,
                    language="python",
                    start_line=line_num,
                    end_line=line_num,
                )

                violation = Counterexample(
                    file_path=file_path,
                    line_number=line_num,
                    snippet=snippet,
                    rule=self.rule_id,
                    violation_type="trailing_whitespace",
                    severity="low",
                    metadata={
                        "issue": "trailing_whitespace",
                        "column": len(line.rstrip()) + 1,
                    },
                )
                violations.append(violation)

            # Check for line length (assuming 120 char limit)
            if len(line) > 120:
                snippet = CodeSnippet(
                    content=line,
                    language="python",
                    start_line=line_num,
                    end_line=line_num,
                )

                violation = Counterexample(
                    file_path=file_path,
                    line_number=line_num,
                    snippet=snippet,
                    rule=self.rule_id,
                    violation_type="line_too_long",
                    severity="low",
                    metadata={
                        "issue": "line_too_long",
                        "length": len(line),
                        "limit": 120,
                    },
                )
                violations.append(violation)

        return violations


class RuleEngine:
    """Engine for running compliance rules."""

    def __init__(self):
        self.rules: List[Any] = []
        self.enabled_rules: Set[str] = set()

    def add_rule(self, rule: Any):
        """Add a rule to the engine."""
        self.rules.append(rule)
        if hasattr(rule, "rule_id"):
            self.enabled_rules.add(rule.rule_id)

    def enable_rule(self, rule_id: str):
        """Enable a rule."""
        self.enabled_rules.add(rule_id)

    def disable_rule(self, rule_id: str):
        """Disable a rule."""
        self.enabled_rules.discard(rule_id)

    def check_file(self, file_path: str, content: str) -> List[Counterexample]:
        """Check a file against all enabled rules."""
        all_violations = []

        for rule in self.rules:
            if hasattr(rule, "rule_id") and rule.rule_id in self.enabled_rules:
                try:
                    violations = rule.check(file_path, content)
                    all_violations.extend(violations)
                except Exception as e:
                    # Log error but continue with other rules
                    print(f"Error in rule {rule.rule_id}: {e}")

        return all_violations

    def check_files(self, files: Dict[str, str]) -> Dict[str, List[Counterexample]]:
        """Check multiple files."""
        results = {}

        for file_path, content in files.items():
            violations = self.check_file(file_path, content)
            results[file_path] = violations

        return results

    def get_rule_summary(self) -> Dict[str, Any]:
        """Get summary of rules."""
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len(self.enabled_rules),
            "rule_ids": list(self.enabled_rules),
        }


def create_default_rules() -> RuleEngine:
    """Create default set of compliance rules."""
    engine = RuleEngine()

    # Add deprecated API rule
    deprecated_apis = [
        "foo_v1",
        "bar_v1",
        "baz_v1",  # Example deprecated APIs
        "old_function",
        "legacy_method",
        "deprecated_api_call",
    ]
    engine.add_rule(DeprecatedAPIRule(deprecated_apis))

    # Add naming convention rule
    engine.add_rule(NamingConventionRule("snake_case"))

    # Add security rule
    engine.add_rule(SecurityRule())

    # Add code style rule
    engine.add_rule(CodeStyleRule())

    return engine
