"""
Tests pour l'alpha-renaming dans l'e-graph.
"""

from xme.egraph.node import (AlphaRenamer, alpha_rename_expr,
                             is_alpha_equivalent)


def test_alpha_rename_simple():
    """Test d'alpha-renaming simple."""
    expr1 = {"op": "var", "name": "x"}
    expr2 = {"op": "var", "name": "y"}

    renamer = AlphaRenamer()
    renamed1 = alpha_rename_expr(expr1, renamer)
    renamed2 = alpha_rename_expr(expr2, renamer)

    # Les variables doivent être renommées différemment
    assert renamed1["name"] != renamed2["name"]
    assert renamed1["name"] == "_1"
    assert renamed2["name"] == "_2"


def test_alpha_rename_complex():
    """Test d'alpha-renaming avec expression complexe."""
    expr = {"op": "+", "args": [{"op": "var", "name": "x"}, {"op": "var", "name": "y"}]}

    renamer = AlphaRenamer()
    renamed = alpha_rename_expr(expr, renamer)

    # Vérifier la structure
    assert renamed["op"] == "+"
    assert len(renamed["args"]) == 2

    # Vérifier que les variables sont renommées
    var_names = [arg["name"] for arg in renamed["args"] if arg["op"] == "var"]
    assert "_1" in var_names
    assert "_2" in var_names


def test_alpha_equivalent_same_vars():
    """Test que var:x, var:y vs var:a, var:b sont alpha-équivalentes."""
    expr1 = {"op": "+", "args": [{"op": "var", "name": "x"}, {"op": "var", "name": "y"}]}

    expr2 = {"op": "+", "args": [{"op": "var", "name": "a"}, {"op": "var", "name": "b"}]}

    # Les expressions doivent être alpha-équivalentes
    assert is_alpha_equivalent(expr1, expr2)


def test_alpha_equivalent_different_structure():
    """Test que des structures différentes ne sont pas alpha-équivalentes."""
    expr1 = {"op": "+", "args": [{"op": "var", "name": "x"}, {"op": "var", "name": "y"}]}

    expr2 = {"op": "*", "args": [{"op": "var", "name": "x"}, {"op": "var", "name": "y"}]}

    # Les expressions ne doivent pas être alpha-équivalentes
    assert not is_alpha_equivalent(expr1, expr2)


def test_alpha_equivalent_different_var_count():
    """Test que des expressions avec un nombre différent de variables ne sont pas alpha-équivalentes."""
    expr1 = {"op": "+", "args": [{"op": "var", "name": "x"}, {"op": "var", "name": "y"}]}

    expr2 = {"op": "+", "args": [{"op": "var", "name": "x"}]}

    # Les expressions ne doivent pas être alpha-équivalentes
    assert not is_alpha_equivalent(expr1, expr2)


def test_renamer_reset():
    """Test que le renamer peut être remis à zéro."""
    renamer = AlphaRenamer()

    # Premier usage
    expr1 = {"op": "var", "name": "x"}
    renamed1 = alpha_rename_expr(expr1, renamer)
    assert renamed1["name"] == "_1"

    # Reset
    renamer.reset()

    # Deuxième usage
    expr2 = {"op": "var", "name": "y"}
    renamed2 = alpha_rename_expr(expr2, renamer)
    assert renamed2["name"] == "_1"  # Recommence à _1


def test_alpha_rename_nested():
    """Test d'alpha-renaming avec expressions imbriquées."""
    expr = {
        "op": "compose",
        "args": [
            {"op": "+", "args": [{"op": "var", "name": "x"}, {"op": "var", "name": "y"}]},
            {"op": "*", "args": [{"op": "var", "name": "a"}, {"op": "var", "name": "b"}]},
        ],
    }

    renamer = AlphaRenamer()
    renamed = alpha_rename_expr(expr, renamer)

    # Vérifier que toutes les variables sont renommées
    def collect_vars(expr):
        if isinstance(expr, dict) and expr.get("op") == "var":
            return [expr["name"]]
        elif isinstance(expr, dict) and "args" in expr:
            result = []
            for arg in expr["args"]:
                result.extend(collect_vars(arg))
            return result
        return []

    var_names = collect_vars(renamed)
    expected_names = ["_1", "_2", "_3", "_4"]
    assert sorted(var_names) == sorted(expected_names)
