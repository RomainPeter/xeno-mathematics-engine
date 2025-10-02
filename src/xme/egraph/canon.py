"""
Canonicalisation d'expressions avec règles commutatives.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from .node import AlphaRenamer, alpha_rename_expr

# Opérateurs commutatifs
COMMUTATIVE_OPS = {"+", "*", "and", "or", "∧", "∨", "&", "|"}


def canonicalize(expr: Dict[str, Any]) -> Dict[str, Any]:
    """
    Canonicalise une expression.

    Args:
        expr: Expression JSON à canoniser

    Returns:
        Dictionnaire avec 'expr_canon' et 'sig'
    """
    # 1. Alpha-renaming des variables
    renamer = AlphaRenamer()
    expr_alpha = alpha_rename_expr(expr, renamer)

    # 2. Normalisation des arguments pour les opérateurs commutatifs
    expr_normalized = normalize_commutative_args(expr_alpha)

    # 3. Tri des attributs
    expr_canon = sort_attrs(expr_normalized)

    # 4. Génération de la signature
    sig = generate_signature(expr_canon)

    return {"expr_canon": expr_canon, "sig": sig}


def normalize_commutative_args(expr: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalise les arguments pour les opérateurs commutatifs.

    Args:
        expr: Expression à normaliser

    Returns:
        Expression normalisée
    """
    if not isinstance(expr, dict):
        return expr

    op = expr.get("op", "")
    args = expr.get("args", [])
    expr.get("attrs", {})

    # Normaliser récursivement les arguments
    normalized_args = [normalize_commutative_args(arg) for arg in args]

    # Si l'opérateur est commutatif, trier les arguments
    if op in COMMUTATIVE_OPS and len(normalized_args) >= 2:
        # Trier les arguments par leur signature
        args_with_sigs = []
        for arg in normalized_args:
            arg_sig = generate_signature(arg)
            args_with_sigs.append((arg_sig, arg))

        # Trier par signature lexicographique
        args_with_sigs.sort(key=lambda x: x[0])
        sorted_args = [arg for _, arg in args_with_sigs]

        return {**expr, "args": sorted_args}
    else:
        # Opérateur non-commutatif, garder l'ordre original
        return {**expr, "args": normalized_args}


def sort_attrs(expr: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trie les attributs d'une expression.

    Args:
        expr: Expression à trier

    Returns:
        Expression avec attributs triés
    """
    if not isinstance(expr, dict):
        return expr

    # Si c'est une variable ou une constante, la retourner telle quelle
    if "var" in expr or "const" in expr:
        return {k: v for k, v in expr.items() if k not in ("args", "op", "attrs")}

    # Trier récursivement les arguments
    args = expr.get("args", [])
    sorted_args = [sort_attrs(arg) for arg in args]

    # Trier les attributs
    attrs = expr.get("attrs", {})
    sorted_attrs = dict(sorted(attrs.items()))

    return {"op": expr.get("op", ""), "args": sorted_args, "attrs": sorted_attrs}


def generate_signature(expr: Dict[str, Any]) -> str:
    """
    Génère une signature canonique pour une expression.

    Args:
        expr: Expression à signer

    Returns:
        Signature SHA256 hexadécimale
    """
    # Parcours postfix des tokens canoniques
    tokens = postfix_traversal(expr)

    # Sérialiser les tokens
    serialized = json.dumps(tokens, sort_keys=True, separators=(",", ":"))

    # Calculer le hash SHA256
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def postfix_traversal(expr: Dict[str, Any]) -> List[str]:
    """
    Parcours postfix d'une expression pour générer les tokens canoniques.

    Args:
        expr: Expression à parcourir

    Returns:
        Liste des tokens en ordre postfix
    """
    if not isinstance(expr, dict):
        return [str(expr)]

    op = expr.get("op", "")
    args = expr.get("args", [])
    attrs = expr.get("attrs", {})

    tokens = []

    # Parcourir récursivement les arguments
    for arg in args:
        tokens.extend(postfix_traversal(arg))

    # Ajouter l'opérateur
    tokens.append(f"op:{op}")

    # Ajouter les attributs triés
    for key, value in sorted(attrs.items()):
        tokens.append(f"attr:{key}:{json.dumps(value, sort_keys=True)}")

    return tokens


def are_structurally_equal(expr1: Dict[str, Any], expr2: Dict[str, Any]) -> bool:
    """
    Vérifie si deux expressions sont structurellement égales.

    Args:
        expr1: Première expression
        expr2: Deuxième expression

    Returns:
        True si les expressions sont structurellement égales
    """
    canon1 = canonicalize(expr1)
    canon2 = canonicalize(expr2)

    return canon1["sig"] == canon2["sig"]


def compare_expressions(expr1: Dict[str, Any], expr2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare deux expressions et retourne des informations détaillées.

    Args:
        expr1: Première expression
        expr2: Deuxième expression

    Returns:
        Dictionnaire avec les résultats de la comparaison
    """
    canon1 = canonicalize(expr1)
    canon2 = canonicalize(expr2)

    return {
        "equal": canon1["sig"] == canon2["sig"],
        "sig1": canon1["sig"],
        "sig2": canon2["sig"],
        "canon1": canon1["expr_canon"],
        "canon2": canon2["expr_canon"],
    }
