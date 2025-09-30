"""
Delta metrics for structural changes and obligation violations.
"""

from typing import Dict, Set, Tuple, Any
import libcst as cst


def _public_api_sig(code: str) -> Set[Tuple[str, str, int]]:
    """Extract public API signatures from code."""
    try:
        m = cst.parse_module(code)
    except Exception:
        return set()

    names = set()

    class Visitor(cst.CSTVisitor):
        def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
            if not node.name.value.startswith("_"):
                arity = sum(1 for p in node.params.params)
                names.add(("def", node.name.value, arity))

        def visit_ClassDef(self, node: cst.ClassDef) -> None:
            if not node.name.value.startswith("_"):
                names.add(("class", node.name.value))

    m.visit(Visitor())
    return names


def _node_counts(code: str) -> Dict[str, int]:
    """Count different node types in code."""
    try:
        m = cst.parse_module(code)
    except Exception:
        return {"if": 0, "for": 0, "while": 0, "call": 0}

    counts = {"if": 0, "for": 0, "while": 0, "call": 0}

    class Visitor(cst.CSTVisitor):
        def visit_If(self, node: cst.If) -> None:
            counts["if"] += 1

        def visit_For(self, node: cst.For) -> None:
            counts["for"] += 1

        def visit_While(self, node: cst.While) -> None:
            counts["while"] += 1

        def visit_Call(self, node: cst.Call) -> None:
            counts["call"] += 1

    m.visit(Visitor())
    return counts


def _rel_diff(a: int, b: int) -> float:
    """Calculate relative difference between two values."""
    if a == b == 0:
        return 0.0
    denom = max(a, b, 1)
    return abs(a - b) / denom


def delta_struct(
    before: str, after: str, w_api: float = 0.6, w_cf: float = 0.3, w_call: float = 0.1
) -> float:
    """Calculate structural delta between before and after code."""
    api_a = _public_api_sig(before)
    api_b = _public_api_sig(after)
    api_jacc = 1.0 - (len(api_a & api_b) / max(len(api_a | api_b), 1))

    ca = _node_counts(before)
    cb = _node_counts(after)
    cf = _rel_diff(
        ca["if"] + ca["for"] + ca["while"], cb["if"] + cb["for"] + cb["while"]
    )
    call = _rel_diff(ca["call"], cb["call"])

    return min(1.0, w_api * api_jacc + w_cf * cf + w_call * call)


def dK(violations: Dict[str, int], weights: Dict[str, float] = None) -> float:
    """Calculate obligation violation score."""
    w = {"semver": 0.3, "changelog": 0.2, "secrets": 0.3, "egress": 0.3, "dep_pin": 0.2}
    if weights:
        w.update(weights)

    return sum(w[k] * float(violations.get(k, 0)) for k in w.keys())


def delta_run(
    before_code: str,
    after_code: str,
    violations: Dict[str, int],
    weights: Dict[str, Any],
) -> float:
    """Calculate overall delta run score."""
    ds = delta_struct(
        before_code,
        after_code,
        w_api=weights.get("w_api", 0.6),
        w_cf=weights.get("w_cf", 0.3),
        w_call=weights.get("w_call", 0.1),
    )

    dk = dK(violations, weights.get("dK"))

    wH = weights.get("wH", 0.0)
    wE = weights.get("wE", 0.0)
    wK = weights.get("wK", 0.5)
    wA = weights.get("wA", 0.5)
    wJ = weights.get("wJ", 0.0)

    # H/E/J neutral by default; A ~ code structure, K ~ obligations
    return min(1.0, wA * ds + wK * dk + wH * 0 + wE * 0 + wJ * 0)
