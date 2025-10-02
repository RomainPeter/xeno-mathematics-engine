"""
Système de coûts pour E-graph.
"""
from __future__ import annotations
from typing import Dict, Any


def cost_nodes(expr: Dict[str, Any]) -> int:
    """
    Calcule le coût basé sur le nombre de nœuds.
    
    Args:
        expr: Expression à évaluer
    
    Returns:
        Coût (nombre de nœuds)
    """
    if "const" in expr or "var" in expr:
        return 1
    if "op" in expr:
        return 1 + sum(cost_nodes(a) for a in expr.get("args", []))
    return 1


def cost_weighted(weights: Dict[str, int]):
    """
    Crée une fonction de coût pondérée.
    
    Args:
        weights: Dictionnaire des poids par opérateur
    
    Returns:
        Fonction de coût pondérée
    """
    def _cost(expr):
        if "const" in expr or "var" in expr:
            return weights.get("leaf", 1)
        if "op" in expr:
            w = weights.get(expr["op"], 1)
            return w + sum(_cost(a) for a in expr.get("args", []))
        return 1
    
    return _cost
