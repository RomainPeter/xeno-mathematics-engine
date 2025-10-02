"""
Construction de PSP depuis les concepts FCA.
"""
from __future__ import annotations
from typing import List, Tuple, Set
from xme.psp.schema import PSP, Block, Edge, BlockKind


def concepts_to_psp(concepts: List[Tuple[Set[str], Set[str]]]) -> PSP:
    """
    Convertit une liste de concepts (extent, intent) en PSP.
    
    Args:
        concepts: Liste de tuples (extent, intent)
    
    Returns:
        PSP normalisé avec blocs et arêtes
    """
    # Blocs = concepts, id = c{k}, label = "{a,b}"
    blocks = []
    for i, (_, I) in enumerate(concepts):
        label = "{" + ",".join(sorted(I)) + "}"
        blocks.append(Block(
            id=f"c{i}", 
            kind=BlockKind.concept, 
            label=label, 
            data={"intent": sorted(I)}
        ))
    
    # Arêtes: couverture par inclusion stricte d'intents (src intent ⊂ dst intent)
    edges: List[Edge] = []
    for i, (_, I1) in enumerate(concepts):
        for j, (_, I2) in enumerate(concepts):
            if i == j:
                continue
            if set(I1) < set(I2):
                # couverture: pas de K tel que I1 ⊂ Ik ⊂ I2
                covered = False
                for k, (_, Ik) in enumerate(concepts):
                    if k in {i, j}:
                        continue
                    if set(I1) < set(Ik) and set(Ik) < set(I2):
                        covered = True
                        break
                if not covered:
                    edges.append(Edge(src=f"c{i}", dst=f"c{j}", kind="cover"))
    
    psp = PSP(
        blocks=blocks, 
        edges=edges, 
        cuts=[], 
        meta={"theorem": "AE demo"}
    )
    psp.normalize()
    return psp
