"""
Nœuds pour l'e-graph avec alpha-renaming.
"""
from __future__ import annotations
from typing import List, Dict, Any, Union, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod


# Type pour les identifiants de nœuds
NodeId = int


@dataclass
class Node:
    """Nœud dans l'e-graph."""
    op: str
    args: List[NodeId]
    attrs: Dict[str, Any]
    
    def __post_init__(self):
        """Normalise les attributs après initialisation."""
        # Trier les attributs pour la canonicalisation
        self.attrs = dict(sorted(self.attrs.items()))


class Atom(Node):
    """Nœud atomique (symbole ou constante)."""
    
    def __init__(self, symbol: str, attrs: Optional[Dict[str, Any]] = None):
        super().__init__(
            op="atom",
            args=[],
            attrs={"symbol": symbol, **(attrs or {})}
        )


class Value(Node):
    """Nœud valeur (nombres, strings)."""
    
    def __init__(self, value: Union[int, float, str], attrs: Optional[Dict[str, Any]] = None):
        super().__init__(
            op="value",
            args=[],
            attrs={"value": value, **(attrs or {})}
        )


class Variable(Node):
    """Nœud variable avec alpha-renaming."""
    
    def __init__(self, name: str, attrs: Optional[Dict[str, Any]] = None):
        super().__init__(
            op="var",
            args=[],
            attrs={"name": name, **(attrs or {})}
        )


class AlphaRenamer:
    """Gestionnaire d'alpha-renaming pour les variables libres."""
    
    def __init__(self):
        self.var_map: Dict[str, str] = {}
        self.counter = 0
    
    def rename_var(self, var_name: str) -> str:
        """
        Renomme une variable selon l'ordre d'apparition.
        
        Args:
            var_name: Nom de la variable originale
            
        Returns:
            Nom canonique de la variable (var:_1, var:_2, etc.)
        """
        if var_name not in self.var_map:
            self.counter += 1
            self.var_map[var_name] = f"_{self.counter}"
        return self.var_map[var_name]
    
    def reset(self):
        """Remet à zéro le renamer."""
        self.var_map.clear()
        self.counter = 0


def alpha_rename_expr(expr: Dict[str, Any], renamer: Optional[AlphaRenamer] = None) -> Dict[str, Any]:
    """
    Applique l'alpha-renaming à une expression.
    
    Args:
        expr: Expression JSON à renommer
        renamer: Renamer existant (optionnel)
        
    Returns:
        Expression avec variables renommées
    """
    if renamer is None:
        renamer = AlphaRenamer()
    
    if not isinstance(expr, dict):
        return expr
    
    op = expr.get("op")
    
    if "var" in expr:
        # Renommer la variable
        name = expr.get("var", "")
        new_name = renamer.rename_var(name)
        return {
            "var": new_name,
            **{k: v for k, v in expr.items() if k not in ("var")}
        }
    
    elif op in ["atom", "value"]:
        # Les atomes et valeurs ne sont pas renommés
        return expr
    
    else:
        # Opérateur avec arguments
        args = expr.get("args", [])
        renamed_args = [alpha_rename_expr(arg, renamer) for arg in args]
        
        return {
            **expr,
            "args": renamed_args
        }


def extract_variables(expr: Dict[str, Any]) -> List[str]:
    """
    Extrait toutes les variables d'une expression.
    
    Args:
        expr: Expression JSON
        
    Returns:
        Liste des noms de variables (sans doublons)
    """
    variables = set()
    
    def _extract(expr):
        if not isinstance(expr, dict):
            return
        
        op = expr.get("op")
        if op == "var":
            variables.add(expr.get("name", ""))
        elif "args" in expr:
            for arg in expr["args"]:
                _extract(arg)
    
    _extract(expr)
    return sorted(list(variables))


def is_alpha_equivalent(expr1: Dict[str, Any], expr2: Dict[str, Any]) -> bool:
    """
    Vérifie si deux expressions sont alpha-équivalentes.
    
    Args:
        expr1: Première expression
        expr2: Deuxième expression
        
    Returns:
        True si les expressions sont alpha-équivalentes
    """
    # Extraire les variables de chaque expression
    vars1 = extract_variables(expr1)
    vars2 = extract_variables(expr2)
    
    # Si le nombre de variables est différent, pas alpha-équivalentes
    if len(vars1) != len(vars2):
        return False
    
    # Appliquer l'alpha-renaming aux deux expressions
    renamer1 = AlphaRenamer()
    renamer2 = AlphaRenamer()
    
    renamed1 = alpha_rename_expr(expr1, renamer1)
    renamed2 = alpha_rename_expr(expr2, renamer2)
    
    # Comparer les expressions renommées
    return renamed1 == renamed2
