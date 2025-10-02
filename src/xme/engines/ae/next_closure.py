"""
Implémentation de Next-Closure avec ordre lectique (Ganter).
"""
from __future__ import annotations
from typing import List, Set, Tuple
from xme.engines.ae.context import FCAContext
from xme.utils.fca import intent_of, extent_of


def lectic_next(ctx: FCAContext, A: Set[str], attrs: List[str]) -> Set[str] | None:
    """
    Calcule le prochain intent dans l'ordre lectique.
    
    Args:
        ctx: Contexte FCA
        A: Intent actuel
        attrs: Liste des attributs triés
    
    Returns:
        Prochain intent ou None si fin
    """
    # Ganter's Next-Closure
    A_sorted = [a for a in attrs if a in A]
    Aset = set(A_sorted)
    
    for i in range(len(attrs)-1, -1, -1):
        a = attrs[i]
        if a in Aset:
            continue
        
        B = set(x for x in Aset if attrs.index(x) < i) | {a}
        B_cl = intent_of(ctx, B)
        
        # Check lectic condition: max({x in B_cl \ A | x < a}) == a
        diff = [x for x in B_cl if x not in Aset and attrs.index(x) <= i]
        if diff and max(diff, key=lambda x: attrs.index(x)) == a:
            return B_cl
    
    return None


def enumerate_concepts(ctx: FCAContext) -> List[Tuple[Set[str], Set[str]]]:
    """
    Énumère tous les concepts FCA via Next-Closure.
    
    Args:
        ctx: Contexte FCA
    
    Returns:
        Liste de concepts (extent, intent) triés
    """
    attrs = sorted(ctx.attributes)
    intents: List[Set[str]] = []
    
    # Commencer avec l'intent vide
    A = intent_of(ctx, set())
    intents.append(A)
    
    # Itérer avec Next-Closure
    while True:
        A = lectic_next(ctx, A, attrs)
        if A is None:
            break
        if A in intents:
            break
        intents.append(A)
    
    # Construire couples (extent, intent)
    concepts: List[Tuple[Set[str], Set[str]]] = []
    for I in intents:
        E = extent_of(ctx, I)
        concepts.append((E, I))
    
    # Tri stable: par |I|, puis lex
    concepts.sort(key=lambda c: (len(c[1]), tuple(sorted(c[1]))))
    
    return concepts
