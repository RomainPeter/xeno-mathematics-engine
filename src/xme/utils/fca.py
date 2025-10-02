"""
Utilitaires FCA (Formal Concept Analysis).
"""
from __future__ import annotations
from typing import Set, List, Dict, Tuple
from xme.engines.ae.context import FCAContext


def intent_of(ctx: FCAContext, A: Set[str]) -> Set[str]:
    """
    Calcule l'intent (fermeture) d'un ensemble d'objets.
    
    Args:
        ctx: Contexte FCA
        A: Ensemble d'objets
    
    Returns:
        Ensemble d'attributs communs à tous les objets de A
    """
    objs = [set(o.attrs) for o in ctx.objects if A.issubset(set(o.attrs))]
    if not objs:
        return set(ctx.attributes)  # convention: fermeture du vide = tous, mais si aucun objet -> tous
    inter = set(ctx.attributes)
    for attrs in objs:
        inter &= attrs
    return inter


def extent_of(ctx: FCAContext, B: Set[str]) -> Set[str]:
    """
    Calcule l'extent d'un ensemble d'attributs.
    
    Args:
        ctx: Contexte FCA
        B: Ensemble d'attributs
    
    Returns:
        Ensemble d'objets qui possèdent tous les attributs de B
    """
    return {o.id for o in ctx.objects if B.issubset(set(o.attrs))}
