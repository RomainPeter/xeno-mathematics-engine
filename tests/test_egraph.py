"""
Tests for e-graph rules and canonicalization.
"""

import os
# Import our modules
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from methods.egraph.canonicalize import (EGraphCanonicalizer,
                                         canonicalize_choreography,
                                         canonicalize_state)
from methods.egraph.rules import EGraphRules, EquivalenceRule


class TestEGraphRules:
    """Test e-graph rules functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rules = EGraphRules()

    def test_initialize_rules(self):
        """Test rule initialization."""
        assert len(self.rules.rules) > 0
        assert all(isinstance(rule, EquivalenceRule) for rule in self.rules.rules)

        # Check categories
        categories = set(rule.category for rule in self.rules.rules)
        expected_categories = {
            "idempotence",
            "guarded_commutation",
            "associativity",
            "commutativity",
            "absorption",
            "local_absorption",
        }
        assert categories == expected_categories

    def test_get_rules_by_category(self):
        """Test getting rules by category."""
        idempotence_rules = self.rules.get_rules_by_category("idempotence")
        assert len(idempotence_rules) == 3  # Normalize, Verify, Meet

        commutation_rules = self.rules.get_rules_by_category("guarded_commutation")
        assert len(commutation_rules) == 2  # Normalize↔Retrieve, Verify↔Normalize

    def test_get_safe_rules_v0_1(self):
        """Test getting safe rules v0.1."""
        safe_rules = self.rules.get_safe_rules_v0_1()
        assert len(safe_rules) > 0

        # All rules should be in safe categories
        safe_categories = {
            "idempotence",
            "guarded_commutation",
            "associativity",
            "commutativity",
            "absorption",
            "local_absorption",
        }
        for rule in safe_rules:
            assert rule.category in safe_categories

    def test_apply_idempotence_rule(self):
        """Test applying idempotence rule."""
        rule = self.rules.get_rules_by_category("idempotence")[0]

        # Test data with duplicate operations
        data = {
            "operations": ["Normalize", "Verify", "Normalize"],
            "type": "choreography",
        }

        result = self.rules.apply_rule(rule, data)

        assert result is not None
        assert "rule_applied" in result
        assert result["rule_applied"] == rule.name

    def test_apply_commutativity_rule(self):
        """Test applying commutativity rule."""
        rule = self.rules.get_rules_by_category("commutativity")[0]

        # Test data with commutative operations
        data = {"operations": ["Meet", "Verify"], "type": "choreography"}

        result = self.rules.apply_rule(rule, data)

        assert result is not None
        assert "rule_applied" in result
        assert result["rule_applied"] == rule.name

    def test_canonicalize_data(self):
        """Test canonicalizing data."""
        data = {
            "operations": ["Normalize", "Verify", "Normalize"],
            "type": "choreography",
        }

        canonical_hash, canonical_rep = self.rules.canonicalize(data)

        assert isinstance(canonical_hash, str)
        assert len(canonical_hash) == 16  # Truncated hash
        assert isinstance(canonical_rep, dict)
        assert canonical_hash in self.rules.equivalence_classes

    def test_get_equivalence_witness(self):
        """Test getting equivalence witness."""
        data = {"operations": ["Normalize", "Verify"]}
        canonical_hash, _ = self.rules.canonicalize(data)

        witness = self.rules.get_equivalence_witness(canonical_hash)

        assert witness is not None
        assert "representative" in witness
        assert "original" in witness
        assert "applied_rules" in witness

    def test_get_stats(self):
        """Test getting e-graph statistics."""
        stats = self.rules.get_stats()

        assert "total_rules" in stats
        assert "safe_rules_v0_1" in stats
        assert "equivalence_classes" in stats
        assert "categories" in stats

        assert stats["total_rules"] > 0
        assert stats["safe_rules_v0_1"] > 0


class TestEGraphCanonicalizer:
    """Test e-graph canonicalizer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canonicalizer = EGraphCanonicalizer()

    def test_canonicalize_state(self):
        """Test canonicalizing a cognitive state."""
        state = {
            "H": {"imp1": {"premises": ["A"], "conclusions": ["B"]}},
            "E": {"cex1": {"data": "counterexample"}},
            "K": {"rule1": {"content": "test rule"}},
            "A": {"attr1": "value1"},
            "operations": ["Normalize", "Verify"],
        }

        canonical_hash, canonical_rep = self.canonicalizer.canonicalize_state(state)

        assert isinstance(canonical_hash, str)
        assert isinstance(canonical_rep, dict)
        assert canonical_hash in self.canonicalizer.equivalence_witnesses

    def test_canonicalize_choreography(self):
        """Test canonicalizing a choreography."""
        choreography = {
            "id": "choreo1",
            "operations": ["Normalize", "Verify", "Normalize"],
            "pre_conditions": ["pre1"],
            "post_conditions": ["post1"],
            "guards": ["guard1"],
        }

        canonical_hash, canonical_rep = self.canonicalizer.canonicalize_choreography(choreography)

        assert isinstance(canonical_hash, str)
        assert isinstance(canonical_rep, dict)
        assert canonical_hash in self.canonicalizer.equivalence_witnesses

    def test_get_equivalence_witness(self):
        """Test getting equivalence witness."""
        state = {"operations": ["Normalize", "Verify"]}
        canonical_hash, _ = self.canonicalizer.canonicalize_state(state)

        witness = self.canonicalizer.get_equivalence_witness(canonical_hash)

        assert witness is not None
        assert "original_state" in witness
        assert "canonical_hash" in witness
        assert "canonical_representative" in witness

    def test_find_equivalent_states(self):
        """Test finding equivalent states."""
        state1 = {"operations": ["Normalize", "Verify"]}
        state2 = {"operations": ["Verify", "Normalize"]}  # Should be equivalent

        hash1, _ = self.canonicalizer.canonicalize_state(state1)
        hash2, _ = self.canonicalizer.canonicalize_state(state2)

        equivalent1 = self.canonicalizer.find_equivalent_states(hash1)
        equivalent2 = self.canonicalizer.find_equivalent_states(hash2)

        assert len(equivalent1) >= 1
        assert len(equivalent2) >= 1

    def test_get_canonical_stats(self):
        """Test getting canonicalization statistics."""
        stats = self.canonicalizer.get_canonical_stats()

        assert "total_canonicalized" in stats
        assert "equivalence_witnesses" in stats
        assert "rules_stats" in stats
        assert "cache_hit_rate" in stats


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_canonicalize_state_function(self):
        """Test canonicalize_state convenience function."""
        state = {"operations": ["Normalize", "Verify"]}

        canonical_hash, canonical_rep = canonicalize_state(state)

        assert isinstance(canonical_hash, str)
        assert isinstance(canonical_rep, dict)

    def test_canonicalize_choreography_function(self):
        """Test canonicalize_choreography convenience function."""
        choreography = {
            "operations": ["Normalize", "Verify", "Normalize"],
            "pre_conditions": ["pre1"],
        }

        canonical_hash, canonical_rep = canonicalize_choreography(choreography)

        assert isinstance(canonical_hash, str)
        assert isinstance(canonical_rep, dict)


class TestEGraphAcceptanceCriteria:
    """Test e-graph acceptance criteria."""

    def test_eclass_id_stable(self):
        """Test that canonicalize() produces stable eclass_id."""
        canonicalizer = EGraphCanonicalizer()

        # Same data should produce same canonical hash
        data1 = {"operations": ["Normalize", "Verify"]}
        data2 = {"operations": ["Normalize", "Verify"]}

        hash1, _ = canonicalizer.canonicalize_state(data1)
        hash2, _ = canonicalizer.canonicalize_state(data2)

        assert hash1 == hash2, "Same data should produce same canonical hash"

    def test_equivalence_witness_stored(self):
        """Test that equivalence witness is stored in Journal."""
        canonicalizer = EGraphCanonicalizer()

        state = {"operations": ["Normalize", "Verify"]}
        canonical_hash, canonical_rep = canonicalizer.canonicalize_state(state)

        # Get witness
        witness = canonicalizer.get_equivalence_witness(canonical_hash)

        assert witness is not None
        assert "original_state" in witness
        assert "canonical_hash" in witness
        assert "canonical_representative" in witness
        assert "timestamp" in witness
        assert "rules_applied" in witness

        print("✅ E-graph Acceptance Criteria Met:")
        print(f"   - Stable eclass_id: {canonical_hash}")
        print(f"   - Equivalence witness stored: {len(witness)} fields")
        print(f"   - Rules applied: {witness.get('rules_applied', [])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
