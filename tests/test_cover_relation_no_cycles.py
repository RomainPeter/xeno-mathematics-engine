"""
Tests pour la relation de couverture sans cycles.
"""

import networkx as nx

from xme.engines.ae.context import load_context
from xme.engines.ae.next_closure import enumerate_concepts
from xme.engines.ae.psp_builder import concepts_to_psp


def test_cover_relation_is_dag():
    """Test que la relation de couverture forme un DAG."""
    ctx = load_context("tests/fixtures/fca/context_4x4.json")
    concepts = enumerate_concepts(ctx)
    psp = concepts_to_psp(concepts)

    g = nx.DiGraph()
    for b in psp.blocks:
        g.add_node(b.id)
    for e in psp.edges:
        g.add_edge(e.src, e.dst)

    assert nx.is_directed_acyclic_graph(g)


def test_cover_relation_is_dag_5x3():
    """Test que la relation de couverture forme un DAG pour le contexte 5x3."""
    ctx = load_context("tests/fixtures/fca/context_5x3.json")
    concepts = enumerate_concepts(ctx)
    psp = concepts_to_psp(concepts)

    g = nx.DiGraph()
    for b in psp.blocks:
        g.add_node(b.id)
    for e in psp.edges:
        g.add_edge(e.src, e.dst)

    assert nx.is_directed_acyclic_graph(g)
