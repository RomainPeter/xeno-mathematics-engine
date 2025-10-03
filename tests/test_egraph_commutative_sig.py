"""
Tests pour les signatures commutatives dans l'e-graph.
"""

from xme.egraph.canon import are_structurally_equal, canonicalize


def test_commutative_addition():
    """Test que add_comm.json vs swapped ont la même signature."""
    expr1 = {"op": "+", "args": [{"op": "var", "name": "x"}, {"op": "var", "name": "y"}]}

    expr2 = {"op": "+", "args": [{"op": "var", "name": "y"}, {"op": "var", "name": "x"}]}

    # Les expressions doivent être structurellement égales
    assert are_structurally_equal(expr1, expr2)

    # Vérifier les signatures
    canon1 = canonicalize(expr1)
    canon2 = canonicalize(expr2)
    assert canon1["sig"] == canon2["sig"]


def test_commutative_multiplication():
    """Test que la multiplication commutative fonctionne."""
    expr1 = {
        "op": "*",
        "args": [{"op": "value", "attrs": {"value": 2}}, {"op": "value", "attrs": {"value": 3}}],
    }

    expr2 = {
        "op": "*",
        "args": [{"op": "value", "attrs": {"value": 3}}, {"op": "value", "attrs": {"value": 2}}],
    }

    assert are_structurally_equal(expr1, expr2)


def test_commutative_logical_and():
    """Test que le ET logique est commutatif."""
    expr1 = {"op": "and", "args": [{"op": "var", "name": "p"}, {"op": "var", "name": "q"}]}

    expr2 = {"op": "and", "args": [{"op": "var", "name": "q"}, {"op": "var", "name": "p"}]}

    assert are_structurally_equal(expr1, expr2)


def test_commutative_logical_or():
    """Test que le OU logique est commutatif."""
    expr1 = {"op": "or", "args": [{"op": "var", "name": "a"}, {"op": "var", "name": "b"}]}

    expr2 = {"op": "or", "args": [{"op": "var", "name": "b"}, {"op": "var", "name": "a"}]}

    assert are_structurally_equal(expr1, expr2)


def test_commutative_unicode_operators():
    """Test que les opérateurs Unicode sont commutatifs."""
    expr1 = {"op": "∧", "args": [{"op": "var", "name": "x"}, {"op": "var", "name": "y"}]}

    expr2 = {"op": "∧", "args": [{"op": "var", "name": "y"}, {"op": "var", "name": "x"}]}

    assert are_structurally_equal(expr1, expr2)


def test_commutative_three_args():
    """Test que la commutativité fonctionne avec 3 arguments."""
    expr1 = {
        "op": "+",
        "args": [
            {"op": "var", "name": "a"},
            {"op": "var", "name": "b"},
            {"op": "var", "name": "c"},
        ],
    }

    expr2 = {
        "op": "+",
        "args": [
            {"op": "var", "name": "c"},
            {"op": "var", "name": "a"},
            {"op": "var", "name": "b"},
        ],
    }

    assert are_structurally_equal(expr1, expr2)


def test_commutative_nested():
    """Test que la commutativité fonctionne avec des expressions imbriquées."""
    expr1 = {
        "op": "+",
        "args": [
            {"op": "*", "args": [{"op": "var", "name": "x"}, {"op": "var", "name": "y"}]},
            {"op": "*", "args": [{"op": "var", "name": "a"}, {"op": "var", "name": "b"}]},
        ],
    }

    expr2 = {
        "op": "+",
        "args": [
            {"op": "*", "args": [{"op": "var", "name": "a"}, {"op": "var", "name": "b"}]},
            {"op": "*", "args": [{"op": "var", "name": "y"}, {"op": "var", "name": "x"}]},
        ],
    }

    assert are_structurally_equal(expr1, expr2)


def test_non_commutative_operators():
    """Test que les opérateurs non-commutatifs ne sont pas traités comme commutatifs."""
    # Utiliser des valeurs différentes pour éviter l'alpha-renaming
    expr1 = {
        "op": "-",
        "args": [{"op": "value", "attrs": {"value": 1}}, {"op": "value", "attrs": {"value": 2}}],
    }

    expr2 = {
        "op": "-",
        "args": [{"op": "value", "attrs": {"value": 2}}, {"op": "value", "attrs": {"value": 1}}],
    }

    # La soustraction n'est pas commutative
    assert not are_structurally_equal(expr1, expr2)


def test_signature_stability():
    """Test que les signatures sont stables (même entrée → même signature)."""
    expr = {"op": "+", "args": [{"op": "var", "name": "x"}, {"op": "var", "name": "y"}]}

    canon1 = canonicalize(expr)
    canon2 = canonicalize(expr)

    # Les signatures doivent être identiques
    assert canon1["sig"] == canon2["sig"]
    assert canon1["expr_canon"] == canon2["expr_canon"]
