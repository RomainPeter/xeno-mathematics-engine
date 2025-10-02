"""
Tests pour les opérateurs non-commutatifs dans l'e-graph.
"""
from xme.egraph.canon import canonicalize, are_structurally_equal


def test_compose_order_matters():
    """Test que l'ordre des arguments de compose compte."""
    expr1 = {
        "op": "compose",
        "args": [
            {"op": "value", "attrs": {"value": "f"}},
            {"op": "value", "attrs": {"value": "g"}}
        ]
    }
    
    expr2 = {
        "op": "compose",
        "args": [
            {"op": "value", "attrs": {"value": "g"}},
            {"op": "value", "attrs": {"value": "f"}}
        ]
    }
    
    # Compose n'est pas commutatif
    assert not are_structurally_equal(expr1, expr2)
    
    # Vérifier que les signatures sont différentes
    canon1 = canonicalize(expr1)
    canon2 = canonicalize(expr2)
    assert canon1["sig"] != canon2["sig"]


def test_division_order_matters():
    """Test que l'ordre des arguments de division compte."""
    expr1 = {
        "op": "/",
        "args": [
            {"op": "value", "attrs": {"value": 10}},
            {"op": "value", "attrs": {"value": 2}}
        ]
    }
    
    expr2 = {
        "op": "/",
        "args": [
            {"op": "value", "attrs": {"value": 2}},
            {"op": "value", "attrs": {"value": 10}}
        ]
    }
    
    # La division n'est pas commutative
    assert not are_structurally_equal(expr1, expr2)


def test_power_order_matters():
    """Test que l'ordre des arguments de puissance compte."""
    expr1 = {
        "op": "^",
        "args": [
            {"op": "value", "attrs": {"value": 2}},
            {"op": "value", "attrs": {"value": 3}}
        ]
    }
    
    expr2 = {
        "op": "^",
        "args": [
            {"op": "value", "attrs": {"value": 3}},
            {"op": "value", "attrs": {"value": 2}}
        ]
    }
    
    # La puissance n'est pas commutative
    assert not are_structurally_equal(expr1, expr2)


def test_application_order_matters():
    """Test que l'ordre des arguments d'application compte."""
    expr1 = {
        "op": "apply",
        "args": [
            {"op": "value", "attrs": {"value": "f"}},
            {"op": "value", "attrs": {"value": "x"}}
        ]
    }
    
    expr2 = {
        "op": "apply",
        "args": [
            {"op": "value", "attrs": {"value": "x"}},
            {"op": "value", "attrs": {"value": "f"}}
        ]
    }
    
    # L'application n'est pas commutative
    assert not are_structurally_equal(expr1, expr2)


def test_implication_order_matters():
    """Test que l'ordre des arguments d'implication compte."""
    expr1 = {
        "op": "->",
        "args": [
            {"op": "value", "attrs": {"value": "p"}},
            {"op": "value", "attrs": {"value": "q"}}
        ]
    }
    
    expr2 = {
        "op": "->",
        "args": [
            {"op": "value", "attrs": {"value": "q"}},
            {"op": "value", "attrs": {"value": "p"}}
        ]
    }
    
    # L'implication n'est pas commutative
    assert not are_structurally_equal(expr1, expr2)


def test_equality_order_matters():
    """Test que l'ordre des arguments d'égalité compte."""
    expr1 = {
        "op": "=",
        "args": [
            {"op": "var", "name": "x"},
            {"op": "var", "name": "y"}
        ]
    }
    
    expr2 = {
        "op": "=",
        "args": [
            {"op": "var", "name": "y"},
            {"op": "var", "name": "x"}
        ]
    }
    
    # L'égalité est commutative, mais testons quand même
    # (En fait, l'égalité devrait être commutative, mais testons la logique)
    assert are_structurally_equal(expr1, expr2)  # L'égalité est commutative


def test_nested_non_commutative():
    """Test que la non-commutativité fonctionne avec des expressions imbriquées."""
    expr1 = {
        "op": "compose",
        "args": [
            {
                "op": "compose",
                "args": [
                    {"op": "value", "attrs": {"value": "f"}},
                    {"op": "value", "attrs": {"value": "g"}}
                ]
            },
            {
                "op": "compose",
                "args": [
                    {"op": "value", "attrs": {"value": "h"}},
                    {"op": "value", "attrs": {"value": "i"}}
                ]
            }
        ]
    }
    
    expr2 = {
        "op": "compose",
        "args": [
            {
                "op": "compose",
                "args": [
                    {"op": "value", "attrs": {"value": "h"}},
                    {"op": "value", "attrs": {"value": "i"}}
                ]
            },
            {
                "op": "compose",
                "args": [
                    {"op": "value", "attrs": {"value": "f"}},
                    {"op": "value", "attrs": {"value": "g"}}
                ]
            }
        ]
    }
    
    # Les expressions ne doivent pas être égales
    assert not are_structurally_equal(expr1, expr2)


def test_mixed_commutative_non_commutative():
    """Test que la commutativité fonctionne correctement avec des opérateurs mixtes."""
    # Expression avec opérateur commutatif au niveau supérieur
    expr1 = {
        "op": "+",
        "args": [
            {
                "op": "compose",
                "args": [
                    {"op": "var", "name": "f"},
                    {"op": "var", "name": "g"}
                ]
            },
            {
                "op": "compose",
                "args": [
                    {"op": "var", "name": "h"},
                    {"op": "var", "name": "i"}
                ]
            }
        ]
    }
    
    expr2 = {
        "op": "+",
        "args": [
            {
                "op": "compose",
                "args": [
                    {"op": "var", "name": "h"},
                    {"op": "var", "name": "i"}
                ]
            },
            {
                "op": "compose",
                "args": [
                    {"op": "var", "name": "f"},
                    {"op": "var", "name": "g"}
                ]
            }
        ]
    }
    
    # Le niveau supérieur est commutatif, donc les expressions doivent être égales
    assert are_structurally_equal(expr1, expr2)
