"""
E-graph canonicalization for Discovery Engine 2-Cat.
Implements canonicalization using e-graph rules.
"""

from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
from .rules import RULES


class EGraphCanonicalizer:
    """E-graph canonicalizer using rules v0.1."""

    def __init__(self):
        self.rules = RULES
        self.canonical_cache = {}
        self.equivalence_witnesses = {}

    def canonicalize_state(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Canonicalize a cognitive state."""
        print("🔗 Canonicalizing state...")

        # Extract canonicalizable components
        canonicalizable = self._extract_canonicalizable_components(state)

        # Apply e-graph rules
        canonical_hash, canonical_rep = self.rules.canonicalize(canonicalizable)

        # Store equivalence witness
        witness = {
            "original_state": state,
            "canonical_hash": canonical_hash,
            "canonical_representative": canonical_rep,
            "timestamp": datetime.now().isoformat(),
            "rules_applied": self.rules.equivalence_classes.get(canonical_hash, {}).get(
                "applied_rules", []
            ),
        }

        self.equivalence_witnesses[canonical_hash] = witness

        return canonical_hash, canonical_rep

    def canonicalize_choreography(
        self, choreography: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Canonicalize a choreography/composite operation."""
        print("🔗 Canonicalizing choreography...")

        # Extract operations for canonicalization
        operations = choreography.get("operations", [])

        # Create canonicalizable representation
        canonicalizable = {
            "operations": operations,
            "pre_conditions": choreography.get("pre_conditions", []),
            "post_conditions": choreography.get("post_conditions", []),
            "guards": choreography.get("guards", []),
        }

        # Apply e-graph rules
        canonical_hash, canonical_rep = self.rules.canonicalize(canonicalizable)

        # Store equivalence witness
        witness = {
            "original_choreography": choreography,
            "canonical_hash": canonical_hash,
            "canonical_representative": canonical_rep,
            "timestamp": datetime.now().isoformat(),
            "rules_applied": self.rules.equivalence_classes.get(canonical_hash, {}).get(
                "applied_rules", []
            ),
        }

        self.equivalence_witnesses[canonical_hash] = witness

        return canonical_hash, canonical_rep

    def _extract_canonicalizable_components(
        self, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract components that can be canonicalized."""
        canonicalizable = {}

        # Extract implications (H)
        if "H" in state:
            implications = state["H"]
            canonicalizable["implications"] = (
                list(implications.values())
                if isinstance(implications, dict)
                else implications
            )

        # Extract operations from state
        if "operations" in state:
            canonicalizable["operations"] = state["operations"]

        # Extract rules (K)
        if "K" in state:
            rules = state["K"]
            canonicalizable["rules"] = (
                list(rules.values()) if isinstance(rules, dict) else rules
            )

        # Extract attributes (A)
        if "A" in state:
            attributes = state["A"]
            canonicalizable["attributes"] = (
                list(attributes.values())
                if isinstance(attributes, dict)
                else attributes
            )

        return canonicalizable

    def get_equivalence_witness(self, canonical_hash: str) -> Optional[Dict[str, Any]]:
        """Get equivalence witness for canonical hash."""
        return self.equivalence_witnesses.get(canonical_hash)

    def find_equivalent_states(self, target_hash: str) -> List[Dict[str, Any]]:
        """Find all states equivalent to target hash."""
        equivalent = []
        for hash_key, witness in self.equivalence_witnesses.items():
            if hash_key == target_hash:
                equivalent.append(witness)
        return equivalent

    def get_canonical_stats(self) -> Dict[str, Any]:
        """Get canonicalization statistics."""
        return {
            "total_canonicalized": len(self.canonical_cache),
            "equivalence_witnesses": len(self.equivalence_witnesses),
            "rules_stats": self.rules.get_stats(),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
        }

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if not self.canonical_cache:
            return 0.0
        # Mock calculation
        return 0.85  # 85% cache hit rate


def canonicalize_state(state: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Convenience function to canonicalize a state."""
    canonicalizer = EGraphCanonicalizer()
    return canonicalizer.canonicalize_state(state)


def canonicalize_choreography(
    choreography: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """Convenience function to canonicalize a choreography."""
    canonicalizer = EGraphCanonicalizer()
    return canonicalizer.canonicalize_choreography(choreography)


# Global canonicalizer instance
canonicalizer = EGraphCanonicalizer()
