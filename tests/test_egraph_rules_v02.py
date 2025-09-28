#!/usr/bin/env python3
"""
Tests for E-graph Rules v0.2
Tests the new v0.2 rules: Normalize∘Verify commute and Meet absorption with K disjoint
"""
import pytest
from methods.egraph.rules import EGraphRules


class TestEGraphRulesV02:
    """Test suite for E-graph rules v0.2"""

    def setup_method(self):
        """Setup test instance"""
        self.rules = EGraphRules()

    def test_normalize_verify_commute_rule(self):
        """Test Normalize∘Verify commute under strict guard"""
        # Test data with Normalize∘Verify pattern
        test_data = {
            "operations": ["Normalize", "Verify"],
            "guard": "strict",
            "type": "composition",
        }

        # Get the v0.2 commutation rule
        v02_rules = [
            rule for rule in self.rules.rules if rule.category == "v0.2_commutation"
        ]
        assert len(v02_rules) > 0, "v0.2 commutation rules should exist"

        # Test rule application
        result = self.rules.apply_rule(v02_rules[0], test_data)
        assert result is not None, "Rule should be applicable"
        assert "rule_applied" in result, "Rule should be applied"

    def test_meet_absorption_local_rule(self):
        """Test Meet absorption with K disjoint"""
        # Test data with Meet pattern and disjoint K sets
        test_data = {
            "operations": ["Meet"],
            "K_left": {"rule1", "rule2"},
            "K_right": {"rule3", "rule4"},
            "type": "meet",
        }

        # Get the v0.2 absorption rule
        v02_rules = [
            rule for rule in self.rules.rules if rule.category == "v0.2_absorption"
        ]
        assert len(v02_rules) > 0, "v0.2 absorption rules should exist"

        # Test rule application
        result = self.rules.apply_rule(v02_rules[0], test_data)
        assert result is not None, "Rule should be applicable"

    def test_v02_rules_categories(self):
        """Test that v0.2 rule categories exist"""
        categories = set(rule.category for rule in self.rules.rules)

        assert (
            "v0.2_commutation" in categories
        ), "v0.2_commutation category should exist"
        assert "v0.2_absorption" in categories, "v0.2_absorption category should exist"

    def test_v02_rules_count(self):
        """Test that v0.2 rules are properly added"""
        v02_commutation_rules = [
            rule for rule in self.rules.rules if rule.category == "v0.2_commutation"
        ]
        v02_absorption_rules = [
            rule for rule in self.rules.rules if rule.category == "v0.2_absorption"
        ]

        assert (
            len(v02_commutation_rules) >= 1
        ), "Should have at least 1 v0.2 commutation rule"
        assert (
            len(v02_absorption_rules) >= 1
        ), "Should have at least 1 v0.2 absorption rule"

    def test_rule_guards_v02(self):
        """Test that v0.2 rules have proper guards"""
        v02_rules = [
            rule for rule in self.rules.rules if rule.category.startswith("v0.2")
        ]

        for rule in v02_rules:
            assert rule.guard is not None, f"Rule {rule.name} should have a guard"
            assert (
                "pre_condition" in rule.guard
            ), f"Rule {rule.name} should have pre_condition"

    def test_canonicalization_with_v02_rules(self):
        """Test canonicalization includes v0.2 rules"""
        test_data = {
            "operations": ["Normalize", "Verify"],
            "guard": "strict",
            "type": "composition",
        }

        # Test canonicalization
        canonical_hash, canonical_data = self.rules.canonicalize(test_data)

        assert canonical_hash is not None, "Canonical hash should be generated"
        assert canonical_data is not None, "Canonical data should be generated"

        # Check that v0.2 rules are considered
        stats = self.rules.get_stats()
        assert "total_rules" in stats, "Stats should include total rules count"

    def test_equivalence_witness_v02(self):
        """Test equivalence witness for v0.2 rules"""
        test_data = {
            "operations": ["Meet"],
            "K_left": {"rule1"},
            "K_right": {"rule2"},
            "type": "meet",
        }

        canonical_hash, canonical_data = self.rules.canonicalize(test_data)
        witness = self.rules.get_equivalence_witness(canonical_hash)

        assert witness is not None, "Equivalence witness should exist"
        assert "applied_rules" in witness, "Witness should include applied rules"


if __name__ == "__main__":
    pytest.main([__file__])
