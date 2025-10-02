"""
Tests pour Next-Closure sur de petits contextes.
"""
import orjson
from pathlib import Path
from xme.engines.ae.context import load_context
from xme.engines.ae.next_closure import enumerate_concepts


def intents_sorted(concepts):
    """Extrait et trie les intents des concepts."""
    return [sorted(list(I)) for (_, I) in concepts]


def test_next_closure_matches_golden_4x4():
    """Test que Next-Closure produit les intents attendus pour le contexte 4x4."""
    ctx = load_context("tests/fixtures/fca/context_4x4.json")
    concepts = enumerate_concepts(ctx)
    got = intents_sorted(concepts)
    exp = orjson.loads(Path("tests/golden/ae/context_4x4.intents.json").read_bytes())
    assert got == exp


def test_next_closure_matches_golden_5x3():
    """Test que Next-Closure produit les intents attendus pour le contexte 5x3."""
    ctx = load_context("tests/fixtures/fca/context_5x3.json")
    concepts = enumerate_concepts(ctx)
    got = intents_sorted(concepts)
    exp = orjson.loads(Path("tests/golden/ae/context_5x3.intents.json").read_bytes())
    assert got == exp


def test_next_closure_no_duplicates_and_sorted():
    """Test que Next-Closure ne produit pas de doublons et trie correctement."""
    ctx = load_context("tests/fixtures/fca/context_5x3.json")
    concepts = enumerate_concepts(ctx)
    seen = set()
    for _, I in concepts:
        key = tuple(sorted(I))
        assert key not in seen
        seen.add(key)
