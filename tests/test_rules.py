#!/usr/bin/env python3
"""
Tests for incident→rule governance
"""
import json
from pathlib import Path
from typing import Dict, Any, List


class RuleTester:
    """Test rules generated from incidents"""

    def __init__(self, rules_dir: str = "rules"):
        self.rules_dir = Path(rules_dir)
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict[str, Any]]:
        """Load all rules from rules directory"""
        rules = []
        for rule_file in self.rules_dir.glob("*.json"):
            if rule_file.name == "README.md":
                continue
            with open(rule_file, "r") as f:
                rule_data = json.load(f)
                rules.append(rule_data)
        return rules

    def test_rule_coverage(self):
        """Test that rules cover expected incidents"""
        expected_incidents = [
            "s2_secret_injection",
            "s2_missing_semver",
            "s2_flaky_test",
            "s2_breaking_api",
            "s2_race_condition",
            "s2_path_traversal",
            "s2_vulnerable_dependency",
        ]

        covered_incidents = set()
        for rule in self.rules:
            if "source_incident" in rule:
                covered_incidents.add(rule["source_incident"])

        missing_incidents = set(expected_incidents) - covered_incidents
        assert (
            len(missing_incidents) == 0
        ), f"Missing rules for incidents: {missing_incidents}"

        print(f"✅ All {len(expected_incidents)} incidents covered by rules")

    def test_rule_structure(self):
        """Test that rules have required structure"""
        required_fields = [
            "id",
            "title",
            "description",
            "category",
            "severity",
            "test_cases",
        ]

        for rule in self.rules:
            for field in required_fields:
                assert (
                    field in rule
                ), f"Rule {rule.get('id', 'unknown')} missing field: {field}"

            # Test cases must have required structure
            for test_case in rule["test_cases"]:
                assert (
                    "name" in test_case
                ), f"Test case missing name in rule {rule['id']}"
                assert (
                    "description" in test_case
                ), f"Test case missing description in rule {rule['id']}"
                assert (
                    "expected" in test_case
                ), f"Test case missing expected in rule {rule['id']}"
                assert test_case["expected"] in [
                    "pass",
                    "fail",
                ], f"Invalid expected value in rule {rule['id']}"

        print(f"✅ All {len(self.rules)} rules have valid structure")

    def test_rule_implementation(self):
        """Test that rules have implementation details"""
        for rule in self.rules:
            assert "implementation" in rule, f"Rule {rule['id']} missing implementation"

            impl = rule["implementation"]
            assert "type" in impl, f"Rule {rule['id']} missing implementation type"
            assert impl["type"] in [
                "opa",
                "pytest",
                "static_analysis",
            ], f"Invalid implementation type in rule {rule['id']}"
            assert "file" in impl, f"Rule {rule['id']} missing implementation file"
            assert (
                "command" in impl
            ), f"Rule {rule['id']} missing implementation command"

        print(f"✅ All {len(self.rules)} rules have implementation details")

    def test_obligation_consistency(self):
        """Test that rule obligations are consistent"""
        all_obligations = set()
        for rule in self.rules:
            if "obligations" in rule:
                all_obligations.update(rule["obligations"])

        # Check that obligations start with 'k-'
        for obligation in all_obligations:
            assert obligation.startswith(
                "k-"
            ), f"Obligation {obligation} should start with 'k-'"

        print(f"✅ All {len(all_obligations)} obligations are properly formatted")

    def run_all_tests(self):
        """Run all rule tests"""
        print("🧪 Testing incident→rule governance...")

        self.test_rule_coverage()
        self.test_rule_structure()
        self.test_rule_implementation()
        self.test_obligation_consistency()

        print("✅ All rule tests passed!")


def main():
    """CLI entry point for rule testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Test incident→rule governance")
    parser.add_argument("--rules-dir", help="Rules directory", default="rules")

    args = parser.parse_args()

    tester = RuleTester(args.rules_dir)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
