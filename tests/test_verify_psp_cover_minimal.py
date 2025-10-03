"""
Tests pour les vérifications PSP S1 (couverture Hasse minimale).
"""

from xme.verifier.base import Verifier, create_obligation
from xme.verifier.psp_checks import get_psp_obligations


def test_psp_hasse_minimal_valid():
    """Test qu'une couverture Hasse minimale valide passe la vérification."""
    # PSP avec couverture minimale (pas d'arêtes transitives)
    minimal_psp = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"},
            {"id": "block3", "kind": "theorem", "content": "C"},
        ],
        "edges": [{"src": "block1", "dst": "block2"}, {"src": "block2", "dst": "block3"}],
    }

    verifier = Verifier()
    for obligation_id, level, check_func, description in get_psp_obligations():
        if level == "S1":
            obligation = create_obligation(obligation_id, level, check_func, description)
            verifier.register_obligation(obligation)

    report = verifier.run_by_level(minimal_psp, "S1")

    # La vérification Hasse minimale doit passer
    hasse_result = next((r for r in report.results if r.obligation_id == "psp_hasse_minimal"), None)
    assert hasse_result is not None
    assert hasse_result.ok
    assert "minimal" in hasse_result.details.get("message", "").lower()


def test_psp_hasse_minimal_with_transitive_edge():
    """Test qu'une couverture avec arête transitive échoue la vérification."""
    # PSP avec arête transitive: block1 -> block2 -> block3, plus block1 -> block3
    transitive_psp = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"},
            {"id": "block3", "kind": "theorem", "content": "C"},
        ],
        "edges": [
            {"src": "block1", "dst": "block2"},
            {"src": "block2", "dst": "block3"},
            {"src": "block1", "dst": "block3"},  # Arête transitive!
        ],
    }

    verifier = Verifier()
    for obligation_id, level, check_func, description in get_psp_obligations():
        if level == "S1":
            obligation = create_obligation(obligation_id, level, check_func, description)
            verifier.register_obligation(obligation)

    report = verifier.run_by_level(transitive_psp, "S1")

    # La vérification Hasse minimale doit échouer
    hasse_result = next((r for r in report.results if r.obligation_id == "psp_hasse_minimal"), None)
    assert hasse_result is not None
    assert not hasse_result.ok
    assert "transitive" in hasse_result.details.get("message", "").lower()


def test_psp_blocks_edges_consistency_valid():
    """Test que la cohérence blocs/arêtes valide passe la vérification."""
    consistent_psp = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"},
        ],
        "edges": [{"src": "block1", "dst": "block2"}],
    }

    verifier = Verifier()
    for obligation_id, level, check_func, description in get_psp_obligations():
        if level == "S1":
            obligation = create_obligation(obligation_id, level, check_func, description)
            verifier.register_obligation(obligation)

    report = verifier.run_by_level(consistent_psp, "S1")

    # La vérification cohérence doit passer
    consistency_result = next(
        (r for r in report.results if r.obligation_id == "psp_blocks_edges_consistency"), None
    )
    assert consistency_result is not None
    assert consistency_result.ok
    assert "consistent" in consistency_result.details.get("message", "").lower()


def test_psp_blocks_edges_consistency_self_loop():
    """Test que les auto-boucles échouent la vérification."""
    self_loop_psp = {
        "blocks": [{"id": "block1", "kind": "axiom", "content": "A"}],
        "edges": [{"src": "block1", "dst": "block1"}],  # Auto-boucle!
    }

    verifier = Verifier()
    for obligation_id, level, check_func, description in get_psp_obligations():
        if level == "S1":
            obligation = create_obligation(obligation_id, level, check_func, description)
            verifier.register_obligation(obligation)

    report = verifier.run_by_level(self_loop_psp, "S1")

    # La vérification cohérence doit échouer
    consistency_result = next(
        (r for r in report.results if r.obligation_id == "psp_blocks_edges_consistency"), None
    )
    assert consistency_result is not None
    assert not consistency_result.ok
    assert "acyclic" in consistency_result.details.get("message", "").lower()


def test_psp_hasse_minimal_complex():
    """Test une couverture Hasse complexe mais minimale."""
    # PSP avec structure en diamant mais minimale
    diamond_psp = {
        "blocks": [
            {"id": "top", "kind": "axiom", "content": "Top"},
            {"id": "left", "kind": "lemma", "content": "Left"},
            {"id": "right", "kind": "lemma", "content": "Right"},
            {"id": "bottom", "kind": "theorem", "content": "Bottom"},
        ],
        "edges": [
            {"src": "top", "dst": "left"},
            {"src": "top", "dst": "right"},
            {"src": "left", "dst": "bottom"},
            {"src": "right", "dst": "bottom"},
        ],
    }

    verifier = Verifier()
    for obligation_id, level, check_func, description in get_psp_obligations():
        if level == "S1":
            obligation = create_obligation(obligation_id, level, check_func, description)
            verifier.register_obligation(obligation)

    report = verifier.run_by_level(diamond_psp, "S1")

    # La vérification Hasse minimale doit passer
    hasse_result = next((r for r in report.results if r.obligation_id == "psp_hasse_minimal"), None)
    assert hasse_result is not None
    assert hasse_result.ok
    assert "minimal" in hasse_result.details.get("message", "").lower()
