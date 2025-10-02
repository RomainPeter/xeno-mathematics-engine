"""
Tests pour la commutativité et associativité menant à la même forme canonique.
"""
from xme.egraph.engine import saturate, extract_best
from xme.egraph.rules import Rule
from xme.egraph.cost import cost_nodes
from xme.egraph.canon import canonicalize


def test_comm_assoc_lead_to_same_best():
    """Test que (a+b)+c et c+(b+a) mènent à la même forme extraite."""
    rules = [
        Rule(lhs={"op": "+", "args": [{"var": "x"}, {"var": "y"}]}, 
             rhs={"op": "+", "args": [{"var": "y"}, {"var": "x"}]}),
        Rule(lhs={"op": "+", "args": [{"op": "+", "args": [{"var": "x"}, {"var": "y"}]}, {"var": "z"}]},
             rhs={"op": "+", "args": [{"var": "x"}, {"op": "+", "args": [{"var": "y"}, {"var": "z"}]}]}),
    ]
    e1 = {"op": "+", "args": [{"op": "+", "args": [{"var": "a"}, {"var": "b"}]}, {"var": "c"}]}
    e2 = {"op": "+", "args": [{"var": "c"}, {"op": "+", "args": [{"var": "b"}, {"var": "a"}]}]}
    
    f1 = extract_best(saturate(e1, rules, max_iters=20), cost_fn=cost_nodes)
    f2 = extract_best(saturate(e2, rules, max_iters=20), cost_fn=cost_nodes)
    
    s1 = canonicalize(f1)["sig"]
    s2 = canonicalize(f2)["sig"]
    assert s1 == s2


def test_commutativity_preserves_equivalence():
    """Test que x+y et y+x ont la même signature canonique."""
    e1 = {"op": "+", "args": [{"var": "x"}, {"var": "y"}]}
    e2 = {"op": "+", "args": [{"var": "y"}, {"var": "x"}]}
    
    s1 = canonicalize(e1)["sig"]
    s2 = canonicalize(e2)["sig"]
    assert s1 == s2


def test_associativity_preserves_equivalence():
    """Test que (x+y)+z et x+(y+z) ont la même signature canonique."""
    e1 = {"op": "+", "args": [{"op": "+", "args": [{"var": "x"}, {"var": "y"}]}, {"var": "z"}]}
    e2 = {"op": "+", "args": [{"var": "x"}, {"op": "+", "args": [{"var": "y"}, {"var": "z"}]}]}
    
    s1 = canonicalize(e1)["sig"]
    s2 = canonicalize(e2)["sig"]
    assert s1 == s2


def test_multiplication_commutativity():
    """Test que x*y et y*x ont la même signature canonique."""
    e1 = {"op": "*", "args": [{"var": "x"}, {"var": "y"}]}
    e2 = {"op": "*", "args": [{"var": "y"}, {"var": "x"}]}
    
    s1 = canonicalize(e1)["sig"]
    s2 = canonicalize(e2)["sig"]
    assert s1 == s2
