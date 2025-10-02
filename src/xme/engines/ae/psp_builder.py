"""
Construction de PSP depuis les concepts FCA avec relation de couverture Hasse.
"""

from __future__ import annotations

from typing import List, Set, Tuple

from xme.psp.schema import PSP, Block, BlockKind, Edge


def hasse_covers(intents: List[Set[str]]) -> List[tuple[int, int]]:
    """
    Calcule les relations de couverture Hasse entre intents.

    Args:
        intents: Liste des intents triés

    Returns:
        Liste des couples (i, j) où intent[i] couvre intent[j]
    """
    covers = []
    n = len(intents)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            I1, I2 = intents[i], intents[j]
            if I1 < I2:
                # check couverture: pas d'intermédiaire
                if not any(I1 < Ik < I2 for k, Ik in enumerate(intents) if k not in (i, j)):
                    covers.append((i, j))

    return covers


def concepts_to_psp(concepts: List[Tuple[Set[str], Set[str]]]) -> PSP:
    """
    Convertit une liste de concepts (extent, intent) en PSP avec couverture Hasse.

    Args:
        concepts: Liste de tuples (extent, intent)

    Returns:
        PSP normalisé avec blocs et arêtes de couverture
    """
    blocks: List[Block] = []
    intents = [I for (_, I) in concepts]

    # Créer les blocs
    for i, (_, I) in enumerate(concepts):
        blocks.append(
            Block(
                id=f"c{i}",
                kind=BlockKind.concept,
                label="{" + ",".join(sorted(I)) + "}",
                data={"intent": sorted(I)},
            )
        )

    # Créer les arêtes de couverture
    covers = hasse_covers(intents)
    edges = [Edge(src=f"c{i}", dst=f"c{j}", kind="cover") for (i, j) in covers]

    psp = PSP(blocks=blocks, edges=edges, cuts=[], meta={"theorem": "AE Next-Closure"})
    psp.normalize()
    return psp
