from xme.psp.schema import PSP


def test_topo_order_respects_edges():
    p = PSP(
        blocks=[
            {"id": "A", "kind": "object"},
            {"id": "B", "kind": "object"},
            {"id": "C", "kind": "object"},
        ],
        edges=[{"src": "A", "dst": "B"}, {"src": "B", "dst": "C"}],
        cuts=[],
        meta={},
    )
    order = p.topo_sort()
    assert order.index("A") < order.index("B") < order.index("C")
