import orjson

from xme.psp.schema import PSP


def test_normalize_idempotent():
    data = {
        "blocks": [{"id": "b", "kind": "lemma"}, {"id": "a", "kind": "axiom"}],
        "edges": [{"src": "b", "dst": "a"}],
        "cuts": [{"id": "c1", "blocks": ["b", "a"]}],
        "meta": {},
    }
    p = PSP(**data)
    j1 = p.normalize().canonical_json()
    p2 = PSP(**orjson.loads(j1)).normalize()
    j2 = p2.canonical_json()
    assert j1 == j2
