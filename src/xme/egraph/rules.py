"""
DSL de patterns et réécriture pour E-graph.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

Expr = Dict[str, Any]  # {"op": str, "args": [Expr,...]} | {"var": str} | {"const": Any}


def is_var(p: Expr) -> bool:
    """Vérifie si une expression est une variable."""
    return "var" in p


def is_const(p: Expr) -> bool:
    """Vérifie si une expression est une constante."""
    return "const" in p


def is_op(p: Expr) -> bool:
    """Vérifie si une expression est une opération."""
    return "op" in p and "args" in p


def match(
    expr: Expr, pat: Expr, env: Optional[Dict[str, Expr]] = None
) -> Optional[Dict[str, Expr]]:
    """
    Match une expression contre un pattern.

    Args:
        expr: Expression à matcher
        pat: Pattern à appliquer
        env: Environnement de variables (optionnel)

    Returns:
        Environnement de variables si match réussi, None sinon
    """
    env = {} if env is None else dict(env)

    if is_var(pat):
        v = pat["var"]
        if v in env:
            return env if env[v] == expr else None
        env[v] = expr
        return env

    if is_const(pat):
        return env if is_const(expr) and expr["const"] == pat["const"] else None

    if is_op(pat):
        if not is_op(expr) or expr["op"] != pat["op"] or len(expr["args"]) != len(pat["args"]):
            return None
        for e_child, p_child in zip(expr["args"], pat["args"]):
            env = match(e_child, p_child, env)
            if env is None:
                return None
        return env

    return None


def substitute(pat: Expr, env: Dict[str, Expr]) -> Expr:
    """
    Substitue les variables dans un pattern avec l'environnement.

    Args:
        pat: Pattern avec variables
        env: Environnement de variables

    Returns:
        Expression avec variables substituées
    """
    if is_var(pat):
        return env[pat["var"]]
    if is_const(pat):
        return {"const": pat["const"]}
    if is_op(pat):
        return {"op": pat["op"], "args": [substitute(a, env) for a in pat["args"]]}
    raise ValueError("bad pattern")


class Rule:
    """Règle de réécriture avec pattern LHS -> RHS."""

    def __init__(self, lhs: Expr, rhs: Expr, name: str = ""):
        """
        Initialise une règle de réécriture.

        Args:
            lhs: Pattern de gauche (Left Hand Side)
            rhs: Pattern de droite (Right Hand Side)
            name: Nom de la règle
        """
        self.lhs, self.rhs, self.name = lhs, rhs, name or "rule"

    def apply(self, expr: Expr) -> Tuple[bool, Expr]:
        """
        Applique la règle à une expression (DFS apply-first).

        Args:
            expr: Expression à réécrire

        Returns:
            Tuple (changed, new_expr) où changed indique si une réécriture a eu lieu
        """
        # Essayer de matcher directement
        m = match(expr, self.lhs)
        if m is not None:
            return True, substitute(self.rhs, m)

        # Si c'est une opération, appliquer récursivement aux arguments
        if is_op(expr):
            changed = False
            new_args: List[Expr] = []
            for a in expr["args"]:
                ch, na = self.apply(a)
                changed = changed or ch
                new_args.append(na)
            if changed:
                return True, {"op": expr["op"], "args": new_args}

        return False, expr
