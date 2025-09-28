"""
E-graph implementation for canonicalization and anti-redundancy.
Implements idempotence and guarded commutations for safe equivalence classes.
"""

from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass
from enum import Enum
import hashlib
import json


class OperatorType(Enum):
    """Core operators from the unified architecture."""

    MEET = "∧"
    GENERALIZE = "↑"
    SPECIALIZE = "↓"
    CONTRAST = "Δ"
    REFUTE = "⊥"
    NORMALIZE = "□"
    VERIFY = "№"
    ABDUCE = "⟂"


@dataclass
class ENode:
    """Node in the e-graph representing an operation or state."""

    id: str
    operator: Optional[OperatorType]
    children: List[str]  # IDs of child nodes
    metadata: Dict[str, Any]
    canonical_id: Optional[str] = None  # Points to canonical representative


@dataclass
class EClass:
    """Equivalence class containing equivalent nodes."""

    canonical_id: str
    members: Set[str]
    properties: Dict[str, Any]


class EGraph:
    """
    E-graph for canonicalizing states and choreographies.
    Implements safe equivalence rules with proofs.
    """

    def __init__(self):
        self.nodes: Dict[str, ENode] = {}
        self.classes: Dict[str, EClass] = {}
        self.rules: List[EQuivalenceRule] = []
        self._initialize_safe_rules()

    def _initialize_safe_rules(self):
        """Initialize the minimal safe ruleset."""
        self.rules = [
            EQuivalenceRule(
                name="idempotence_normalize",
                pattern=lambda n: n.operator == OperatorType.NORMALIZE,
                equivalent=lambda n: n,  # □∘□ = □
                guard=lambda n, ctx: ctx.get("K_fixed", False),
                proof="Normalize is idempotent when constraints K are fixed",
            ),
            EQuivalenceRule(
                name="idempotence_verify",
                pattern=lambda n: n.operator == OperatorType.VERIFY,
                equivalent=lambda n: n,  # №∘№ = №
                guard=lambda n, ctx: ctx.get("proof_validated", False),
                proof="Verify is idempotent after proof validation",
            ),
            EQuivalenceRule(
                name="idempotence_meet",
                pattern=lambda n: n.operator == OperatorType.MEET,
                equivalent=lambda n: n,  # ∧∘∧ = ∧
                guard=lambda n, ctx: ctx.get("same_base", False),
                proof="Meet is idempotent on same base",
            ),
            EQuivalenceRule(
                name="commutation_retrieve_normalize",
                pattern=lambda n: self._is_retrieve_normalize_chain(n),
                equivalent=lambda n: self._swap_retrieve_normalize(n),
                guard=lambda n, ctx: ctx.get("K_fixed", False),
                proof="Retrieve and Normalize commute when K is fixed",
            ),
            EQuivalenceRule(
                name="associativity_meet",
                pattern=lambda n: self._is_meet_chain(n),
                equivalent=lambda n: self._reassociate_meet(n),
                guard=lambda n, ctx: ctx.get("K_fixed", False),
                proof="Meet is associative when K is fixed",
            ),
        ]

    def add_node(self, node: ENode) -> str:
        """Add a node to the e-graph and return its canonical ID."""
        self.nodes[node.id] = node

        # Find equivalent nodes using rules
        canonical_id = self._find_canonical(node)
        if canonical_id:
            node.canonical_id = canonical_id
            self.classes[canonical_id].members.add(node.id)
        else:
            # Create new equivalence class
            node.canonical_id = node.id
            self.classes[node.id] = EClass(
                canonical_id=node.id, members={node.id}, properties={}
            )

        return node.canonical_id

    def canonicalize(self, node_id: str) -> str:
        """Get the canonical representative of a node."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")

        node = self.nodes[node_id]
        return node.canonical_id

    def get_equivalence_class(self, node_id: str) -> EClass:
        """Get the equivalence class for a node."""
        canonical_id = self.canonicalize(node_id)
        return self.classes[canonical_id]

    def _find_canonical(self, node: ENode) -> Optional[str]:
        """Find if this node is equivalent to an existing one."""
        for rule in self.rules:
            if rule.pattern(node):
                # Check if guard conditions are met
                context = self._get_context(node)
                if rule.guard(node, context):
                    # Look for equivalent nodes
                    for existing_id, existing_node in self.nodes.items():
                        if (
                            existing_node.operator == node.operator
                            and self._nodes_equivalent(node, existing_node, rule)
                        ):
                            return existing_node.canonical_id
        return None

    def _get_context(self, node: ENode) -> Dict[str, Any]:
        """Get context for guard evaluation."""
        return {
            "K_fixed": node.metadata.get("K_fixed", False),
            "proof_validated": node.metadata.get("proof_validated", False),
            "same_base": node.metadata.get("same_base", False),
        }

    def _nodes_equivalent(self, n1: ENode, n2: ENode, rule: "EQuivalenceRule") -> bool:
        """Check if two nodes are equivalent under a rule."""
        # Basic structural equivalence
        if n1.operator != n2.operator:
            return False

        # Check if rule-specific equivalence holds
        try:
            equiv1 = rule.equivalent(n1)
            equiv2 = rule.equivalent(n2)
            return self._deep_equivalent(equiv1, equiv2)
        except:
            return False

    def _deep_equivalent(self, obj1: Any, obj2: Any) -> bool:
        """Deep equivalence check for objects."""
        if type(obj1) != type(obj2):
            return False

        if isinstance(obj1, dict):
            return set(obj1.keys()) == set(obj2.keys()) and all(
                self._deep_equivalent(obj1[k], obj2[k]) for k in obj1.keys()
            )

        if isinstance(obj1, list):
            return len(obj1) == len(obj2) and all(
                self._deep_equivalent(a, b) for a, b in zip(obj1, obj2)
            )

        return obj1 == obj2

    def _is_retrieve_normalize_chain(self, node: ENode) -> bool:
        """Check if node represents Retrieve∘Normalize chain."""
        # Simplified: check if it's a composite with retrieve then normalize
        return (
            node.metadata.get("composite", False)
            and "retrieve" in str(node.metadata.get("ops", []))
            and "normalize" in str(node.metadata.get("ops", []))
        )

    def _swap_retrieve_normalize(self, node: ENode) -> ENode:
        """Create equivalent node with swapped retrieve/normalize."""
        # Simplified: create new node with swapped operations
        new_metadata = node.metadata.copy()
        ops = new_metadata.get("ops", [])
        if len(ops) >= 2:
            # Swap first two operations
            ops[0], ops[1] = ops[1], ops[0]
            new_metadata["ops"] = ops

        return ENode(
            id=f"{node.id}_swapped",
            operator=node.operator,
            children=node.children,
            metadata=new_metadata,
        )

    def _is_meet_chain(self, node: ENode) -> bool:
        """Check if node represents a meet chain."""
        return node.operator == OperatorType.MEET and len(node.children) >= 2

    def _reassociate_meet(self, node: ENode) -> ENode:
        """Create equivalent node with reassociated meet operations."""
        # Simplified: create new node with reassociated children
        new_children = node.children.copy()
        if len(new_children) >= 3:
            # Reassociate: (A ∧ B) ∧ C -> A ∧ (B ∧ C)
            new_children = [new_children[0], f"({new_children[1]} ∧ {new_children[2]})"]

        return ENode(
            id=f"{node.id}_reassoc",
            operator=node.operator,
            children=new_children,
            metadata=node.metadata,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the e-graph."""
        return {
            "total_nodes": len(self.nodes),
            "total_classes": len(self.classes),
            "avg_class_size": (
                sum(len(c.members) for c in self.classes.values()) / len(self.classes)
                if self.classes
                else 0
            ),
            "rules_applied": len(self.rules),
        }


@dataclass
class EQuivalenceRule:
    """Rule for e-graph equivalence."""

    name: str
    pattern: callable  # Function to match nodes
    equivalent: callable  # Function to create equivalent node
    guard: callable  # Function to check guard conditions
    proof: str  # Proof/justification


def canonicalize_state(state: Dict[str, Any], egraph: EGraph) -> str:
    """
    Canonicalize a cognitive state X using e-graph.
    Returns the canonical ID for the state.
    """
    # Create a node representing the state
    state_hash = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()

    node = ENode(
        id=f"state_{state_hash[:16]}",
        operator=None,  # States don't have operators
        children=[],
        metadata={
            "state_type": "cognitive_state",
            "hash": state_hash,
            "components": list(state.keys()),
        },
    )

    return egraph.add_node(node)


def canonicalize_choreography(ops: List[str], egraph: EGraph) -> str:
    """
    Canonicalize a choreography (sequence of operations) using e-graph.
    Returns the canonical ID for the choreography.
    """
    # Create a node representing the choreography
    choreo_hash = hashlib.sha256("|".join(ops).encode()).hexdigest()

    node = ENode(
        id=f"choreo_{choreo_hash[:16]}",
        operator=None,  # Choreographies are composite
        children=[],
        metadata={
            "choreography": True,
            "ops": ops,
            "hash": choreo_hash,
            "composite": True,
        },
    )

    return egraph.add_node(node)
