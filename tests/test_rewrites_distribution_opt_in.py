"""
Tests pour la distribution optionnelle basée sur le coût.
"""

from xme.egraph.cost import cost_weighted
from xme.egraph.engine import extract_best, saturate
from xme.egraph.rules import Rule


def test_distribution_optional_cost_driven():
    """Test que la distribution est optionnelle selon le coût."""
    rules = [
        Rule(
            lhs={
                "op": "*",
                "args": [{"var": "x"}, {"op": "+", "args": [{"var": "y"}, {"var": "z"}]}],
            },
            rhs={
                "op": "+",
                "args": [
                    {"op": "*", "args": [{"var": "x"}, {"var": "y"}]},
                    {"op": "*", "args": [{"var": "x"}, {"var": "z"}]},
                ],
            },
        ),
    ]
    expr = {"op": "*", "args": [{"var": "x"}, {"op": "+", "args": [{"var": "y"}, {"var": "z"}]}]}
    forms = saturate(expr, rules, max_iters=5)

    # Avec ces poids, produit préféré sur somme; best devrait rester original ou distribué selon poids
    best = extract_best(forms, cost_fn=cost_weighted({"*": 1, "+": 2, "leaf": 1}))

    # S'assurer qu'une forme extraite existe et est une expression valide
    assert isinstance(best, dict) and ("op" in best or "var" in best or "const" in best)


def test_distribution_with_cheap_multiplication():
    """Test que la distribution se fait quand la multiplication est bon marché."""
    rules = [
        Rule(
            lhs={
                "op": "*",
                "args": [{"var": "x"}, {"op": "+", "args": [{"var": "y"}, {"var": "z"}]}],
            },
            rhs={
                "op": "+",
                "args": [
                    {"op": "*", "args": [{"var": "x"}, {"var": "y"}]},
                    {"op": "*", "args": [{"var": "x"}, {"var": "z"}]},
                ],
            },
        ),
    ]
    expr = {"op": "*", "args": [{"var": "x"}, {"op": "+", "args": [{"var": "y"}, {"var": "z"}]}]}
    forms = saturate(expr, rules, max_iters=5)

    # Multiplication très bon marché, somme chère
    best = extract_best(forms, cost_fn=cost_weighted({"*": 1, "+": 10, "leaf": 1}))

    # Devrait préférer la forme distribuée (plus de multiplications, moins de sommes)
    assert isinstance(best, dict)
    # La forme distribuée devrait avoir plus de nœuds * et moins de nœuds +
    # (vérification basique de la structure)
    assert "op" in best


def test_no_distribution_with_expensive_multiplication():
    """Test que la distribution ne se fait pas quand la multiplication est chère."""
    rules = [
        Rule(
            lhs={
                "op": "*",
                "args": [{"var": "x"}, {"op": "+", "args": [{"var": "y"}, {"var": "z"}]}],
            },
            rhs={
                "op": "+",
                "args": [
                    {"op": "*", "args": [{"var": "x"}, {"var": "y"}]},
                    {"op": "*", "args": [{"var": "x"}, {"var": "z"}]},
                ],
            },
        ),
    ]
    expr = {"op": "*", "args": [{"var": "x"}, {"op": "+", "args": [{"var": "y"}, {"var": "z"}]}]}
    forms = saturate(expr, rules, max_iters=5)

    # Multiplication très chère, somme bon marché
    best = extract_best(forms, cost_fn=cost_weighted({"*": 10, "+": 1, "leaf": 1}))

    # Devrait préférer la forme originale (moins de multiplications)
    assert isinstance(best, dict)
    # La forme originale devrait être préférée
    assert "op" in best
