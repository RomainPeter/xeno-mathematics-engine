"""
Hash-consing et E-graph basiques.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
import json


NodeId = int


@dataclass
class EClass:
    """Classe d'équivalence dans l'e-graph."""
    nodes: List[NodeId]
    
    def __post_init__(self):
        """Normalise la liste des nœuds."""
        self.nodes = sorted(list(set(self.nodes)))


class HashCons:
    """Hash-consing pour l'interning des nœuds."""
    
    def __init__(self):
        self._intern: Dict[str, NodeId] = {}
        self._nodes: Dict[NodeId, Dict[str, Any]] = {}
        self._next_id = 0
    
    def _canonical_key(self, node: Dict[str, Any]) -> str:
        """
        Génère une clé canonique pour un nœud.
        
        Args:
            node: Nœud à canoniser
            
        Returns:
            Clé canonique pour l'interning
        """
        op = node.get("op", "")
        args = node.get("args", [])
        attrs = node.get("attrs", {})
        
        # Trier les arguments pour la canonicalisation
        args_sorted = sorted(args)
        
        # Trier les attributs
        attrs_sorted = dict(sorted(attrs.items()))
        
        # Créer la clé canonique
        key_data = {
            "op": op,
            "args": args_sorted,
            "attrs": attrs_sorted
        }
        
        return json.dumps(key_data, sort_keys=True)
    
    def intern(self, node: Dict[str, Any]) -> NodeId:
        """
        Interne un nœud et retourne son ID.
        
        Args:
            node: Nœud à interner
            
        Returns:
            ID du nœud interné
        """
        key = self._canonical_key(node)
        
        if key in self._intern:
            return self._intern[key]
        
        # Créer un nouveau nœud
        node_id = self._next_id
        self._next_id += 1
        
        # Normaliser le nœud
        normalized_node = {
            "op": node.get("op", ""),
            "args": sorted(node.get("args", [])),
            "attrs": dict(sorted(node.get("attrs", {}).items()))
        }
        
        self._intern[key] = node_id
        self._nodes[node_id] = normalized_node
        
        return node_id
    
    def get_node(self, node_id: NodeId) -> Optional[Dict[str, Any]]:
        """
        Récupère un nœud par son ID.
        
        Args:
            node_id: ID du nœud
            
        Returns:
            Nœud ou None si non trouvé
        """
        return self._nodes.get(node_id)
    
    def get_all_nodes(self) -> Dict[NodeId, Dict[str, Any]]:
        """
        Retourne tous les nœuds internés.
        
        Returns:
            Dictionnaire des nœuds par ID
        """
        return self._nodes.copy()
    
    def clear(self):
        """Remet à zéro le hash-consing."""
        self._intern.clear()
        self._nodes.clear()
        self._next_id = 0


class EGraph:
    """E-graph basique avec classes d'équivalence."""
    
    def __init__(self):
        self.hashcons = HashCons()
        self.eclasses: Dict[NodeId, EClass] = {}
        self._next_eclass_id = 0
    
    def add_node(self, node: Dict[str, Any]) -> NodeId:
        """
        Ajoute un nœud à l'e-graph.
        
        Args:
            node: Nœud à ajouter
            
        Returns:
            ID du nœud ajouté
        """
        # Interner le nœud
        node_id = self.hashcons.intern(node)
        
        # Créer ou mettre à jour la classe d'équivalence
        if node_id not in self.eclasses:
            self.eclasses[node_id] = EClass([node_id])
        
        return node_id
    
    def merge(self, node_id1: NodeId, node_id2: NodeId) -> None:
        """
        Fusionne deux nœuds dans la même classe d'équivalence.
        
        Args:
            node_id1: Premier nœud
            node_id2: Deuxième nœud
        """
        if node_id1 == node_id2:
            return
        
        # Récupérer les classes d'équivalence
        eclass1 = self.eclasses.get(node_id1)
        eclass2 = self.eclasses.get(node_id2)
        
        if not eclass1 or not eclass2:
            return
        
        # Fusionner les classes
        merged_nodes = list(set(eclass1.nodes + eclass2.nodes))
        merged_eclass = EClass(merged_nodes)
        
        # Mettre à jour toutes les références
        for node_id in merged_nodes:
            self.eclasses[node_id] = merged_eclass
    
    def find(self, node_id: NodeId) -> NodeId:
        """
        Trouve le représentant canonique d'un nœud.
        
        Args:
            node_id: ID du nœud
            
        Returns:
            ID du représentant canonique
        """
        eclass = self.eclasses.get(node_id)
        if not eclass or not eclass.nodes:
            return node_id
        
        # Retourner le plus petit ID comme représentant
        return min(eclass.nodes)
    
    def are_equal(self, node_id1: NodeId, node_id2: NodeId) -> bool:
        """
        Vérifie si deux nœuds sont dans la même classe d'équivalence.
        
        Args:
            node_id1: Premier nœud
            node_id2: Deuxième nœud
            
        Returns:
            True si les nœuds sont égaux
        """
        return self.find(node_id1) == self.find(node_id2)
    
    def get_eclass(self, node_id: NodeId) -> Optional[EClass]:
        """
        Récupère la classe d'équivalence d'un nœud.
        
        Args:
            node_id: ID du nœud
            
        Returns:
            Classe d'équivalence ou None
        """
        return self.eclasses.get(node_id)
    
    def get_all_eclasses(self) -> Dict[NodeId, EClass]:
        """
        Retourne toutes les classes d'équivalence.
        
        Returns:
            Dictionnaire des classes d'équivalence
        """
        return self.eclasses.copy()
    
    def clear(self):
        """Remet à zéro l'e-graph."""
        self.hashcons.clear()
        self.eclasses.clear()
        self._next_eclass_id = 0


def build_egraph_from_expr(expr: Dict[str, Any], egraph: Optional[EGraph] = None) -> Tuple[EGraph, NodeId]:
    """
    Construit un e-graph à partir d'une expression.
    
    Args:
        expr: Expression JSON
        egraph: E-graph existant (optionnel)
        
    Returns:
        Tuple (e-graph, ID du nœud racine)
    """
    if egraph is None:
        egraph = EGraph()
    
    def _build(expr):
        if not isinstance(expr, dict):
            return None
        
        op = expr.get("op", "")
        args = expr.get("args", [])
        attrs = expr.get("attrs", {})
        
        # Construire récursivement les arguments
        arg_ids = []
        for arg in args:
            arg_id = _build(arg)
            if arg_id is not None:
                arg_ids.append(arg_id)
        
        # Créer le nœud
        node = {
            "op": op,
            "args": arg_ids,
            "attrs": attrs
        }
        
        return egraph.add_node(node)
    
    root_id = _build(expr)
    return egraph, root_id
