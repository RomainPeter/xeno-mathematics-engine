"""
Tests pour la simplification des unités (multiplication par 1, addition de 0).
"""

from xme.egraph.cost import cost_nodes
from xme.egraph.engine import extract_best, saturate
from xme.egraph.rules import Rule


def test_mul_unit_and_add_zero():
    """Test que x*1 + 0 se simplifie en x."""
    from xme.egraph.canon import canonicalize

    rules = [
        Rule(lhs={"op": "*", "args": [{"var": "x"}, {"const": 1}]}, rhs={"var": "x"}),
        Rule(lhs={"op": "+", "args": [{"var": "x"}, {"const": 0}]}, rhs={"var": "x"}),
    ]
    expr = {"op": "+", "args": [{"op": "*", "args": [{"var": "x"}, {"const": 1}]}, {"const": 0}]}
    forms = saturate(expr, rules, max_iters=10)
    best = extract_best(forms, cost_fn=cost_nodes)

    # Comparer les signatures canoniques
    expected = {"var": "x"}
    best_sig = canonicalize(best)["sig"]
    expected_sig = canonicalize(expected)["sig"]
    assert best_sig == expected_sig


def test_add_zero_left():
    """Test que 0 + x se simplifie en x."""
    from xme.egraph.canon import canonicalize

    rules = [
        Rule(lhs={"op": "+", "args": [{"const": 0}, {"var": "x"}]}, rhs={"var": "x"}),
    ]
    expr = {"op": "+", "args": [{"const": 0}, {"var": "x"}]}
    forms = saturate(expr, rules, max_iters=5)
    best = extract_best(forms, cost_fn=cost_nodes)

    # Comparer les signatures canoniques
    expected = {"var": "x"}
    best_sig = canonicalize(best)["sig"]
    expected_sig = canonicalize(expected)["sig"]
    assert best_sig == expected_sig


def test_mul_unit_left():
    """Test que 1 * x se simplifie en x."""
    from xme.egraph.canon import canonicalize

    rules = [
        Rule(lhs={"op": "*", "args": [{"const": 1}, {"var": "x"}]}, rhs={"var": "x"}),
    ]
    expr = {"op": "*", "args": [{"const": 1}, {"var": "x"}]}
    forms = saturate(expr, rules, max_iters=5)
    best = extract_best(forms, cost_fn=cost_nodes)

    # Comparer les signatures canoniques
    expected = {"var": "x"}
    best_sig = canonicalize(best)["sig"]
    expected_sig = canonicalize(expected)["sig"]
    assert best_sig == expected_sig


def test_nested_simplification():
    """Test que (x*1)*1 + 0 se simplifie en x."""
    from xme.egraph.canon import canonicalize

    rules = [
        Rule(lhs={"op": "*", "args": [{"var": "x"}, {"const": 1}]}, rhs={"var": "x"}),
        Rule(lhs={"op": "+", "args": [{"var": "x"}, {"const": 0}]}, rhs={"var": "x"}),
    ]
    expr = {
        "op": "+",
        "args": [
            {"op": "*", "args": [{"op": "*", "args": [{"var": "x"}, {"const": 1}]}, {"const": 1}]},
            {"const": 0},
        ],
    }
    forms = saturate(expr, rules, max_iters=10)
    best = extract_best(forms, cost_fn=cost_nodes)

    # Comparer les signatures canoniques
    expected = {"var": "x"}
    best_sig = canonicalize(best)["sig"]
    expected_sig = canonicalize(expected)["sig"]
    assert best_sig == expected_sig
