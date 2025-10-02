"""
Vérifications PSP S0/S1.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import networkx as nx

from xme.psp.schema import PSP


def check_psp_acyclic(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    S0: Vérifie l'acyclicité du PSP.

    Args:
        payload: Données PSP à vérifier

    Returns:
        Tuple (ok, details)
    """
    try:
        psp = PSP.model_validate(payload)

        # Construire le graphe
        G = nx.DiGraph()

        # Ajouter les nœuds (blocs)
        for block in psp.blocks:
            G.add_node(block.id)

        # Ajouter les arêtes
        for edge in psp.edges:
            G.add_edge(edge.src, edge.dst)

        # Vérifier l'acyclicité
        is_acyclic = nx.is_directed_acyclic_graph(G)

        if is_acyclic:
            return True, {
                "message": "PSP is acyclic",
                "n_blocks": len(psp.blocks),
                "n_edges": len(psp.edges),
            }
        else:
            # Trouver les cycles
            try:
                cycles = list(nx.simple_cycles(G))
                return False, {
                    "message": "PSP contains cycles",
                    "cycles": cycles,
                    "n_blocks": len(psp.blocks),
                    "n_edges": len(psp.edges),
                }
            except Exception:
                return False, {
                    "message": "PSP contains cycles (unable to enumerate)",
                    "n_blocks": len(psp.blocks),
                    "n_edges": len(psp.edges),
                }

    except Exception as e:
        return False, {"message": f"Error validating PSP: {str(e)}", "error": str(e)}


def check_psp_unique_ids(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    S0: Vérifie l'unicité des IDs de blocs.

    Args:
        payload: Données PSP à vérifier

    Returns:
        Tuple (ok, details)
    """
    try:
        psp = PSP.model_validate(payload)

        # Collecter tous les IDs
        block_ids = [block.id for block in psp.blocks]
        edge_srcs = [edge.src for edge in psp.edges]
        edge_dsts = [edge.dst for edge in psp.edges]

        # Vérifier l'unicité des IDs de blocs
        unique_block_ids = set(block_ids)
        if len(unique_block_ids) != len(block_ids):
            duplicates = []
            seen = set()
            for block_id in block_ids:
                if block_id in seen:
                    duplicates.append(block_id)
                else:
                    seen.add(block_id)

            return False, {
                "message": "Duplicate block IDs found",
                "duplicates": duplicates,
                "n_blocks": len(psp.blocks),
            }

        # Vérifier que les arêtes référencent des blocs existants
        missing_srcs = [src for src in edge_srcs if src not in unique_block_ids]
        missing_dsts = [dst for dst in edge_dsts if dst not in unique_block_ids]

        if missing_srcs or missing_dsts:
            return False, {
                "message": "Edges reference non-existent blocks",
                "missing_srcs": missing_srcs,
                "missing_dsts": missing_dsts,
                "n_blocks": len(psp.blocks),
                "n_edges": len(psp.edges),
            }

        return True, {
            "message": "All block IDs are unique and edges are valid",
            "n_blocks": len(psp.blocks),
            "n_edges": len(psp.edges),
        }

    except Exception as e:
        return False, {"message": f"Error validating PSP IDs: {str(e)}", "error": str(e)}


def check_psp_topological_consistency(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    S0: Vérifie la cohérence topologique (optionnel).

    Args:
        payload: Données PSP à vérifier

    Returns:
        Tuple (ok, details)
    """
    try:
        psp = PSP.model_validate(payload)

        # Construire le graphe
        G = nx.DiGraph()
        for block in psp.blocks:
            G.add_node(block.id)
        for edge in psp.edges:
            G.add_edge(edge.src, edge.dst)

        # Vérifier l'acyclicité (prérequis pour le tri topologique)
        if not nx.is_directed_acyclic_graph(G):
            return False, {"message": "Cannot check topological consistency: graph contains cycles"}

        # Calculer l'ordre topologique
        try:
            topo_order = list(nx.topological_sort(G))

            return True, {
                "message": "Topological order is consistent",
                "topo_order": topo_order,
                "n_blocks": len(psp.blocks),
            }
        except nx.NetworkXError:
            return False, {"message": "Topological sorting failed", "n_blocks": len(psp.blocks)}

    except Exception as e:
        return False, {
            "message": f"Error checking topological consistency: {str(e)}",
            "error": str(e),
        }


def check_psp_hasse_minimal_cover(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    S1: Vérifie que la couverture Hasse est minimale (aucune arête couverte).

    Args:
        payload: Données PSP à vérifier

    Returns:
        Tuple (ok, details)
    """
    try:
        psp = PSP.model_validate(payload)

        # Construire le graphe
        G = nx.DiGraph()
        for block in psp.blocks:
            G.add_node(block.id)
        for edge in psp.edges:
            G.add_edge(edge.src, edge.dst)

        # Vérifier l'acyclicité (prérequis)
        if not nx.is_directed_acyclic_graph(G):
            return False, {"message": "Cannot check Hasse cover: graph contains cycles"}

        # Vérifier qu'il n'y a pas d'arêtes transitives
        transitive_edges = []

        # Pour chaque paire de nœuds (u, v), vérifier s'il existe un chemin u -> ... -> v
        for u in G.nodes():
            for v in G.nodes():
                if u != v and G.has_edge(u, v):
                    # Vérifier s'il existe un chemin plus long de u à v
                    try:
                        paths = list(nx.all_simple_paths(G, u, v, cutoff=2))
                        # Si il y a des chemins de longueur > 1, l'arête (u,v) est transitive
                        if any(len(path) > 2 for path in paths):
                            transitive_edges.append((u, v))
                    except nx.NetworkXNoPath:
                        pass

        if transitive_edges:
            return False, {
                "message": "Hasse cover is not minimal: transitive edges found",
                "transitive_edges": transitive_edges,
                "n_edges": len(psp.edges),
            }

        return True, {"message": "Hasse cover is minimal", "n_edges": len(psp.edges)}

    except Exception as e:
        return False, {"message": f"Error checking Hasse cover: {str(e)}", "error": str(e)}


def check_psp_blocks_edges_consistency(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    S1: Vérifie la cohérence entre blocs et arêtes.

    Args:
        payload: Données PSP à vérifier

    Returns:
        Tuple (ok, details)
    """
    try:
        psp = PSP.model_validate(payload)

        # Collecter les IDs de blocs
        block_ids = {block.id for block in psp.blocks}

        # Vérifier que toutes les arêtes référencent des blocs existants
        edge_issues = []
        for edge in psp.edges:
            if edge.src not in block_ids:
                edge_issues.append(
                    f"Edge {edge.src}->{edge.dst}: source block '{edge.src}' not found"
                )
            if edge.dst not in block_ids:
                edge_issues.append(
                    f"Edge {edge.src}->{edge.dst}: destination block '{edge.dst}' not found"
                )

        if edge_issues:
            return False, {
                "message": "Inconsistency between blocks and edges",
                "issues": edge_issues,
                "n_blocks": len(psp.blocks),
                "n_edges": len(psp.edges),
            }

        # Vérifier qu'il n'y a pas d'arêtes auto-référentielles
        self_loops = [edge for edge in psp.edges if edge.src == edge.dst]
        if self_loops:
            return False, {
                "message": "Self-loops found in edges",
                "self_loops": [(edge.src, edge.dst) for edge in self_loops],
                "n_edges": len(psp.edges),
            }

        return True, {
            "message": "Blocks and edges are consistent",
            "n_blocks": len(psp.blocks),
            "n_edges": len(psp.edges),
        }

    except Exception as e:
        return False, {
            "message": f"Error checking blocks/edges consistency: {str(e)}",
            "error": str(e),
        }


def get_psp_obligations() -> List[Tuple[str, str, callable, str]]:
    """
    Retourne toutes les obligations PSP.

    Returns:
        Liste des obligations (id, level, check_func, description)
    """
    return [
        ("psp_acyclic", "S0", check_psp_acyclic, "PSP must be acyclic"),
        ("psp_unique_ids", "S0", check_psp_unique_ids, "PSP block IDs must be unique"),
        (
            "psp_topo_consistency",
            "S0",
            check_psp_topological_consistency,
            "PSP topological order must be consistent",
        ),
        (
            "psp_hasse_minimal",
            "S1",
            check_psp_hasse_minimal_cover,
            "PSP Hasse cover must be minimal",
        ),
        (
            "psp_blocks_edges_consistency",
            "S1",
            check_psp_blocks_edges_consistency,
            "PSP blocks and edges must be consistent",
        ),
    ]
