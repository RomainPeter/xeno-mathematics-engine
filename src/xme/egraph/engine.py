"""
Moteur de saturation et extraction pour E-graph.
"""

from __future__ import annotations

from typing import List, Set

from xme.egraph.canon import canonicalize  # PR #13
from xme.egraph.cost import cost_nodes
from xme.egraph.rules import Expr, Rule


def saturate(
    expr: Expr, rules: List[Rule], max_iters: int = 50, seen_limit: int = 5000
) -> List[Expr]:
    """
    Sature une expression avec des règles de réécriture jusqu'au fixpoint.

    Args:
        expr: Expression initiale
        rules: Liste des règles de réécriture
        max_iters: Nombre maximum d'itérations
        seen_limit: Limite du nombre de formes vues

    Returns:
        Liste des formes canoniques atteignables
    """
    # Explore formes atteignables via réécritures; déduplique par signature canonique
    frontier: List[Expr] = [expr]
    seen_sigs: Set[str] = set()
    results: List[Expr] = []
    iters = 0

    while frontier and iters < max_iters and len(seen_sigs) < seen_limit:
        iters += 1
        next_frontier: List[Expr] = []

        for e in frontier:
            # Canonicaliser et vérifier si déjà vu
            canon_result = canonicalize(e)
            ec = canon_result["expr_canon"]
            sig = canon_result["sig"]
            if sig in seen_sigs:
                continue

            seen_sigs.add(sig)
            results.append(ec)

            # Appliquer toutes les règles
            for r in rules:
                changed, ne = r.apply(e)
                if changed:
                    next_frontier.append(ne)

        frontier = next_frontier

    return results


def extract_best(exprs: List[Expr], cost_fn=cost_nodes) -> Expr:
    """
    Extrait la meilleure forme selon une fonction de coût.

    Args:
        exprs: Liste des expressions candidates
        cost_fn: Fonction de coût (défaut: cost_nodes)

    Returns:
        Expression avec le coût minimal
    """
    if not exprs:
        raise ValueError("No expressions to extract from")

    best = None
    best_c = 10**9

    for e in exprs:
        c = cost_fn(e)
        if c < best_c:
            best, best_c = e, c

    return best
