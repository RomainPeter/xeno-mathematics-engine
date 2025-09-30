"""
E-graph rules v0.1 for Discovery Engine 2-Cat.
Implements safe rules for canonicalization and equivalence.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import json
from datetime import datetime


@dataclass
class EquivalenceRule:
    """Represents an e-graph equivalence rule."""

    name: str
    pattern: str
    guard: Optional[str] = None
    proof_ref: Optional[str] = None
    category: str = "safe_v0.1"


class EGraphRules:
    """E-graph rules v0.1 implementation."""

    def __init__(self):
        self.rules = self._initialize_rules()
        self.equivalence_classes = {}
        self.canonical_representatives = {}

    def _initialize_rules(self) -> List[EquivalenceRule]:
        """Initialize safe rules v0.1."""
        return [
            # Idempotence rules
            EquivalenceRule(
                name="idempotence_normalize",
                pattern="Normalize∘Normalize=Normalize",
                guard="pre_condition: Normalize(x) is defined",
                category="idempotence",
            ),
            EquivalenceRule(
                name="idempotence_verify",
                pattern="Verify∘Verify=Verify",
                guard="pre_condition: Verify(x) is defined",
                category="idempotence",
            ),
            EquivalenceRule(
                name="idempotence_meet",
                pattern="Meet∘Meet=Meet",
                guard="pre_condition: Meet(x,y) is defined",
                category="idempotence",
            ),
            # Guarded commutation rules
            EquivalenceRule(
                name="commutation_normalize_retrieve",
                pattern="Normalize∘Retrieve ↔ Retrieve∘Normalize",
                guard="pre_condition: Normalize(x) and Retrieve(x) are defined; post_condition: same result",
                category="guarded_commutation",
            ),
            EquivalenceRule(
                name="commutation_verify_normalize",
                pattern="Verify∘Normalize ↔ Normalize∘Verify",
                guard="pre_condition: Verify(x) and Normalize(x) are defined; post_condition: same result",
                category="guarded_commutation",
            ),
            # Associativity and commutativity
            EquivalenceRule(
                name="associativity_meet",
                pattern="Meet(Meet(x,y),z) = Meet(x,Meet(y,z))",
                guard="pre_condition: all Meet operations are defined",
                category="associativity",
            ),
            EquivalenceRule(
                name="commutativity_meet",
                pattern="Meet(x,y) = Meet(y,x)",
                guard="pre_condition: Meet(x,y) and Meet(y,x) are defined",
                category="commutativity",
            ),
            # Absorption rules
            EquivalenceRule(
                name="absorption_verify",
                pattern="Verify∘Verify ≡ Verify",
                guard="pre_condition: Verify(x) is defined",
                category="absorption",
            ),
            # Local absorption
            EquivalenceRule(
                name="local_absorption_normalize",
                pattern="Normalize∘Normalize∘Normalize ≡ Normalize",
                guard="pre_condition: Normalize(x) is defined",
                category="local_absorption",
            ),
            # v0.2 rules
            EquivalenceRule(
                name="normalize_verify_commute",
                pattern="Normalize∘Verify ↔ Verify∘Normalize",
                guard="pre_condition: Normalize(x) and Verify(x) are defined; guard: strict",
                category="v0.2_commutation",
            ),
            EquivalenceRule(
                name="meet_absorption_local",
                pattern="Meet(x,Meet(x,y)) ≡ Meet(x,y) when K disjoint",
                guard="pre_condition: K(x) ∩ K(y) = ∅",
                category="v0.2_absorption",
            ),
        ]

    def get_rules_by_category(self, category: str) -> List[EquivalenceRule]:
        """Get rules by category."""
        return [rule for rule in self.rules if rule.category == category]

    def get_safe_rules_v0_1(self) -> List[EquivalenceRule]:
        """Get all safe rules v0.1."""
        return [
            rule
            for rule in self.rules
            if rule.category
            in [
                "idempotence",
                "guarded_commutation",
                "associativity",
                "commutativity",
                "absorption",
                "local_absorption",
            ]
        ]

    def apply_rule(self, rule: EquivalenceRule, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply an equivalence rule to data."""
        print(f"🔗 Applying rule: {rule.name}")

        # Mock rule application
        if rule.category == "idempotence":
            return self._apply_idempotence(rule, data)
        elif rule.category == "guarded_commutation":
            return self._apply_guarded_commutation(rule, data)
        elif rule.category == "associativity":
            return self._apply_associativity(rule, data)
        elif rule.category == "commutativity":
            return self._apply_commutativity(rule, data)
        elif rule.category == "absorption":
            return self._apply_absorption(rule, data)
        else:
            return None

    def _apply_idempotence(self, rule: EquivalenceRule, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply idempotence rule."""
        # Mock: simplify repeated operations
        if "operations" in data:
            ops = data["operations"]
            if len(ops) >= 2 and ops[-1] == ops[-2]:
                simplified_ops = ops[:-1]  # Remove duplicate
                return {**data, "operations": simplified_ops, "rule_applied": rule.name}
        return data

    def _apply_guarded_commutation(
        self, rule: EquivalenceRule, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply guarded commutation rule."""
        # Mock: reorder operations if guards are satisfied
        if "operations" in data and len(data["operations"]) >= 2:
            ops = data["operations"].copy()
            if self._check_guards(rule, data):
                # Swap operations
                ops[-1], ops[-2] = ops[-2], ops[-1]
                return {**data, "operations": ops, "rule_applied": rule.name}
        return data

    def _apply_associativity(self, rule: EquivalenceRule, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply associativity rule."""
        # Mock: regroup operations
        if "operations" in data and len(data["operations"]) >= 3:
            ops = data["operations"].copy()
            # Regroup: (A∘B)∘C → A∘(B∘C)
            if len(ops) >= 3:
                grouped = [ops[0], f"({ops[1]}∘{ops[2]})"]
                return {**data, "operations": grouped, "rule_applied": rule.name}
        return data

    def _apply_commutativity(self, rule: EquivalenceRule, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply commutativity rule."""
        # Mock: swap commutative operations
        if "operations" in data and len(data["operations"]) >= 2:
            ops = data["operations"].copy()
            ops[-1], ops[-2] = ops[-2], ops[-1]
            return {**data, "operations": ops, "rule_applied": rule.name}
        return data

    def _apply_absorption(self, rule: EquivalenceRule, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply absorption rule."""
        # Mock: absorb redundant operations
        if "operations" in data:
            ops = data["operations"]
            if len(ops) >= 2 and ops[-1] == "Verify" and ops[-2] == "Verify":
                absorbed_ops = ops[:-1]  # Remove duplicate Verify
                return {**data, "operations": absorbed_ops, "rule_applied": rule.name}
        return data

    def _check_guards(self, rule: EquivalenceRule, data: Dict[str, Any]) -> bool:
        """Check if rule guards are satisfied."""
        # Mock guard checking
        if "pre_condition" in rule.guard:
            return True  # Assume guards are satisfied for demo
        return False

    def canonicalize(self, data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Canonicalize data using e-graph rules."""
        print("🔗 Canonicalizing data...")

        # Start with original data
        canonical_data = data.copy()
        applied_rules = []

        # Apply all applicable rules
        for rule in self.get_safe_rules_v0_1():
            if self._is_applicable(rule, canonical_data):
                result = self.apply_rule(rule, canonical_data)
                if result and result != canonical_data:
                    canonical_data = result
                    applied_rules.append(rule.name)

        # Generate canonical hash
        canonical_hash = self._calculate_canonical_hash(canonical_data)

        # Store equivalence class
        self.equivalence_classes[canonical_hash] = {
            "representative": canonical_data,
            "original": data,
            "applied_rules": applied_rules,
            "timestamp": datetime.now().isoformat(),
        }

        return canonical_hash, canonical_data

    def _is_applicable(self, rule: EquivalenceRule, data: Dict[str, Any]) -> bool:
        """Check if a rule is applicable to data."""
        # Mock applicability check
        if rule.category == "idempotence":
            return "operations" in data and len(data.get("operations", [])) >= 2
        elif rule.category == "guarded_commutation":
            return "operations" in data and len(data.get("operations", [])) >= 2
        elif rule.category == "associativity":
            return "operations" in data and len(data.get("operations", [])) >= 3
        elif rule.category == "commutativity":
            return "operations" in data and len(data.get("operations", [])) >= 2
        elif rule.category == "absorption":
            return "operations" in data and len(data.get("operations", [])) >= 2
        return False

    def _calculate_canonical_hash(self, data: Dict[str, Any]) -> str:
        """Calculate canonical hash for data."""
        # Sort data for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(sorted_data.encode()).hexdigest()[:16]

    def get_equivalence_witness(self, canonical_hash: str) -> Optional[Dict[str, Any]]:
        """Get equivalence witness for canonical hash."""
        return self.equivalence_classes.get(canonical_hash)

    def get_stats(self) -> Dict[str, Any]:
        """Get e-graph statistics."""
        return {
            "total_rules": len(self.rules),
            "safe_rules_v0_1": len(self.get_safe_rules_v0_1()),
            "equivalence_classes": len(self.equivalence_classes),
            "categories": {
                "idempotence": len(self.get_rules_by_category("idempotence")),
                "guarded_commutation": len(self.get_rules_by_category("guarded_commutation")),
                "associativity": len(self.get_rules_by_category("associativity")),
                "commutativity": len(self.get_rules_by_category("commutativity")),
                "absorption": len(self.get_rules_by_category("absorption")),
                "local_absorption": len(self.get_rules_by_category("local_absorption")),
            },
        }


# Global rules instance
RULES = EGraphRules()
