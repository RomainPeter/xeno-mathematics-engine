#!/usr/bin/env python3
"""
Tests for e-graph rules v0.2
Tests the new safe rules: Normalize∘Verify commute under strict guard, Meet absorption with K disjoint
"""

import pytest

from methods.egraph.rules import EGraphRules


class TestEGraphRulesV02:
    """Test e-graph rules v0.2 functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.egraph = EGraphRules()

    def test_v02_rules_exist(self):
        """Test that v0.2 rules are present."""
        v02_rules = self.egraph.get_rules_by_category("v0.2_commutation")
        v02_absorption = self.egraph.get_rules_by_category("v0.2_absorption")

        assert len(v02_rules) >= 1, "Should have at least 1 v0.2 commutation rule"
        assert len(v02_absorption) >= 1, "Should have at least 1 v0.2 absorption rule"

    def test_normalize_verify_commute_rule(self):
        """Test Normalize∘Verify ↔ Verify∘Normalize rule."""
        rule = next((r for r in self.egraph.rules if r.name == "normalize_verify_commute"), None)
        assert rule is not None, "normalize_verify_commute rule should exist"
        assert "Normalize∘Verify" in rule.pattern
        assert "Verify∘Normalize" in rule.pattern
        assert "guard: strict" in rule.guard

    def test_meet_absorption_local_rule(self):
        """Test Meet absorption with K disjoint rule."""
        rule = next((r for r in self.egraph.rules if r.name == "meet_absorption_local"), None)
        assert rule is not None, "meet_absorption_local rule should exist"
        assert "Meet(x,Meet(x,y))" in rule.pattern
        assert "K(x) ∩ K(y) = ∅" in rule.guard

    def test_normalize_verify_commute_application(self):
        """Test application of Normalize∘Verify commutation rule."""
        test_data = {
            "operations": ["Normalize", "Verify"],
            "context": {"x": "test_value"},
        }

        # Find the rule
        rule = next((r for r in self.egraph.rules if r.name == "normalize_verify_commute"), None)

        if rule and self.egraph._is_applicable(rule, test_data):
            result = self.egraph.apply_rule(rule, test_data)
            assert result is not None, "Rule application should return result"
            assert "rule_applied" in result, "Result should indicate rule was applied"

    def test_meet_absorption_application(self):
        """Test application of Meet absorption rule."""
        test_data = {
            "operations": ["Meet", "Meet"],
            "context": {"x": "value1", "y": "value2", "K_disjoint": True},
        }

        # Find the rule
        rule = next((r for r in self.egraph.rules if r.name == "meet_absorption_local"), None)

        if rule and self.egraph._is_applicable(rule, test_data):
            result = self.egraph.apply_rule(rule, test_data)
            assert result is not None, "Rule application should return result"

    def test_rule_guards_strict(self):
        """Test that v0.2 rules have strict guards."""
        v02_rules = [
            r for r in self.egraph.rules if r.category in ["v0.2_commutation", "v0.2_absorption"]
        ]

        for rule in v02_rules:
            assert rule.guard is not None, f"Rule {rule.name} should have guard"
            assert (
                "strict" in rule.guard or "K(x) ∩ K(y) = ∅" in rule.guard
            ), f"Rule {rule.name} should have strict guard"

    def test_canonicalization_with_v02_rules(self):
        """Test canonicalization using v0.2 rules."""
        test_data = {
            "operations": ["Normalize", "Verify", "Meet"],
            "context": {"x": "test", "y": "other", "K_disjoint": True},
        }

        canonical_hash, canonical_data = self.egraph.canonicalize(test_data)

        assert canonical_hash is not None, "Should generate canonical hash"
        assert canonical_data is not None, "Should generate canonical data"
        assert isinstance(canonical_hash, str), "Canonical hash should be string"
        assert len(canonical_hash) > 0, "Canonical hash should not be empty"

    def test_equivalence_class_storage(self):
        """Test that equivalence classes are stored correctly."""
        test_data = {"operations": ["Normalize", "Verify"], "context": {"x": "test"}}

        canonical_hash, canonical_data = self.egraph.canonicalize(test_data)

        # Check equivalence class was stored
        witness = self.egraph.get_equivalence_witness(canonical_hash)
        assert witness is not None, "Should store equivalence witness"
        assert "representative" in witness, "Witness should have representative"
        assert "applied_rules" in witness, "Witness should track applied rules"

    def test_stats_include_v02_rules(self):
        """Test that stats include v0.2 rules."""
        stats = self.egraph.get_stats()

        assert "total_rules" in stats, "Stats should include total rules"
        assert stats["total_rules"] >= 10, "Should have at least 10 rules including v0.2"

        # Check that v0.2 rules are counted
        v02_count = len(
            [r for r in self.egraph.rules if r.category in ["v0.2_commutation", "v0.2_absorption"]]
        )
        assert v02_count >= 2, "Should have at least 2 v0.2 rules"

    def test_rule_categories_complete(self):
        """Test that all rule categories are properly defined."""
        categories = set(rule.category for rule in self.egraph.rules)

        expected_categories = {
            "idempotence",
            "guarded_commutation",
            "associativity",
            "commutativity",
            "absorption",
            "local_absorption",
            "v0.2_commutation",
            "v0.2_absorption",
        }

        for category in expected_categories:
            assert category in categories, f"Category {category} should be present"

    def test_safe_rules_v01_excludes_v02(self):
        """Test that safe rules v0.1 excludes v0.2 rules."""
        safe_rules = self.egraph.get_safe_rules_v0_1()
        safe_categories = set(rule.category for rule in safe_rules)

        assert "v0.2_commutation" not in safe_categories, "v0.2 rules should not be in safe v0.1"
        assert "v0.2_absorption" not in safe_categories, "v0.2 rules should not be in safe v0.1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
