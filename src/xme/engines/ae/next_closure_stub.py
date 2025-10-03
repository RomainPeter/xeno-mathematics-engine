"""
Stub Next-Closure pour l'énumération de concepts FCA.
"""

from __future__ import annotations

from typing import List, Set, Tuple

from .context import FCAContext


def closure(context: FCAContext, A: Set[str]) -> Set[str]:
    """Calcule la fermeture d'un ensemble d'attributs."""
    objs = [o.attrs for o in context.objects if A.issubset(set(o.attrs))]
    if not objs:
        return set()
    inter = set(objs[0])
    for attrs in objs[1:]:
        inter &= set(attrs)
    return inter


def enumerate_concepts_stub(ctx: FCAContext) -> List[Tuple[Set[str], Set[str]]]:
    """
    Énumère les concepts FCA (extent, intent).
    Stub simplifié : part de ∅ puis ferme des singletons.
    """
    # Très simple: part de ∅ puis ferme des singletons
    intents: List[Set[str]] = []
    intents.append(closure(ctx, set()))
    for a in ctx.attributes[:3]:  # borne courte, stub
        intents.append(closure(ctx, {a}))

    # Uniques et triés par taille puis lexique
    uniq = []
    seen = set()
    for intent in intents:
        key = tuple(sorted(intent))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(intent)

    uniq.sort(key=lambda s: (len(s), tuple(sorted(s))))

    # Extents = objets qui ont l'intent
    res = []
    for intent in uniq:
        extent = {o.id for o in ctx.objects if set(intent).issubset(set(o.attrs))}
        res.append((extent, intent))

    return res
