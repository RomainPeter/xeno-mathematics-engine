"""
Tests pour les vérifications PSP S0.
"""

from xme.verifier.base import Verifier, create_obligation
from xme.verifier.psp_checks import get_psp_obligations


def test_psp_acyclic_valid():
    """Test qu'un PSP acyclique valide passe la vérification."""
    # PSP valide avec 3 blocs et 2 arêtes acycliques
    valid_psp = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"},
            {"id": "block3", "kind": "theorem", "content": "C"},
        ],
        "edges": [{"src": "block1", "dst": "block2"}, {"src": "block2", "dst": "block3"}],
    }

    verifier = Verifier()
    for obligation_id, level, check_func, description in get_psp_obligations():
        if level == "S0":
            obligation = create_obligation(obligation_id, level, check_func, description)
            verifier.register_obligation(obligation)

    report = verifier.run_by_level(valid_psp, "S0")

    assert report.ok_all
    assert len(report.results) >= 2  # Au moins acyclic et unique_ids


def test_psp_acyclic_with_cycle():
    """Test qu'un PSP avec cycle échoue la vérification."""
    # PSP avec cycle: block1 -> block2 -> block3 -> block1
    cyclic_psp = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"},
            {"id": "block3", "kind": "theorem", "content": "C"},
        ],
        "edges": [
            {"src": "block1", "dst": "block2"},
            {"src": "block2", "dst": "block3"},
            {"src": "block3", "dst": "block1"},  # Cycle!
        ],
    }

    verifier = Verifier()
    for obligation_id, level, check_func, description in get_psp_obligations():
        if level == "S0":
            obligation = create_obligation(obligation_id, level, check_func, description)
            verifier.register_obligation(obligation)

    report = verifier.run_by_level(cyclic_psp, "S0")

    # La vérification acyclique doit échouer
    acyclic_result = next((r for r in report.results if r.obligation_id == "psp_acyclic"), None)
    assert acyclic_result is not None
    assert not acyclic_result.ok
    assert "acyclic" in acyclic_result.details.get("message", "").lower()


def test_psp_unique_ids_valid():
    """Test que des IDs uniques passent la vérification."""
    valid_psp = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"},
        ],
        "edges": [{"src": "block1", "dst": "block2"}],
    }

    verifier = Verifier()
    for obligation_id, level, check_func, description in get_psp_obligations():
        if level == "S0":
            obligation = create_obligation(obligation_id, level, check_func, description)
            verifier.register_obligation(obligation)

    report = verifier.run_by_level(valid_psp, "S0")

    # La vérification unique_ids doit passer
    unique_ids_result = next(
        (r for r in report.results if r.obligation_id == "psp_unique_ids"), None
    )
    assert unique_ids_result is not None
    assert unique_ids_result.ok


def test_psp_unique_ids_duplicate():
    """Test que des IDs dupliqués échouent la vérification."""
    duplicate_psp = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block1", "kind": "lemma", "content": "B"},  # ID dupliqué!
        ],
        "edges": [],
    }

    verifier = Verifier()
    for obligation_id, level, check_func, description in get_psp_obligations():
        if level == "S0":
            obligation = create_obligation(obligation_id, level, check_func, description)
            verifier.register_obligation(obligation)

    report = verifier.run_by_level(duplicate_psp, "S0")

    # La vérification unique_ids doit échouer
    unique_ids_result = next(
        (r for r in report.results if r.obligation_id == "psp_unique_ids"), None
    )
    assert unique_ids_result is not None
    assert not unique_ids_result.ok
    assert "duplicate" in unique_ids_result.details.get("message", "").lower()


def test_psp_edges_reference_nonexistent_blocks():
    """Test que des arêtes référençant des blocs inexistants échouent."""
    invalid_psp = {
        "blocks": [{"id": "block1", "kind": "axiom", "content": "A"}],
        "edges": [{"src": "block1", "dst": "nonexistent"}],  # Bloc inexistant!
    }

    verifier = Verifier()
    for obligation_id, level, check_func, description in get_psp_obligations():
        if level == "S0":
            obligation = create_obligation(obligation_id, level, check_func, description)
            verifier.register_obligation(obligation)

    report = verifier.run_by_level(invalid_psp, "S0")

    # La vérification unique_ids doit échouer
    unique_ids_result = next(
        (r for r in report.results if r.obligation_id == "psp_unique_ids"), None
    )
    assert unique_ids_result is not None
    assert not unique_ids_result.ok
    assert "non-existent" in unique_ids_result.details.get("message", "").lower()


def test_psp_topological_consistency():
    """Test la cohérence topologique."""
    valid_psp = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"},
            {"id": "block3", "kind": "theorem", "content": "C"},
        ],
        "edges": [{"src": "block1", "dst": "block2"}, {"src": "block2", "dst": "block3"}],
    }

    verifier = Verifier()
    for obligation_id, level, check_func, description in get_psp_obligations():
        if level == "S0":
            obligation = create_obligation(obligation_id, level, check_func, description)
            verifier.register_obligation(obligation)

    report = verifier.run_by_level(valid_psp, "S0")

    # La vérification topologique doit passer
    topo_result = next(
        (r for r in report.results if r.obligation_id == "psp_topo_consistency"), None
    )
    assert topo_result is not None
    assert topo_result.ok
    assert "consistent" in topo_result.details.get("message", "").lower()
