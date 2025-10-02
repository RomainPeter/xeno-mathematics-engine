"""
Tests pour les métriques δ et leurs bornes.
"""
import pytest
from xme.metrics.delta import (
    compute_delta_ae, compute_delta_cegis, aggregate_run_delta,
    compute_delta_bounds, validate_delta, compute_phase_delta
)


def test_delta_bounds():
    """Test que les δ sont bornés entre 0 et 1."""
    # Test des bornes
    assert compute_delta_bounds(-0.5) == 0.0
    assert compute_delta_bounds(0.0) == 0.0
    assert compute_delta_bounds(0.5) == 0.5
    assert compute_delta_bounds(1.0) == 1.0
    assert compute_delta_bounds(1.5) == 1.0


def test_validate_delta():
    """Test la validation des δ."""
    # Test des valeurs valides
    assert validate_delta(0.0) == 0.0
    assert validate_delta(0.5) == 0.5
    assert validate_delta(1.0) == 1.0
    
    # Test des valeurs hors bornes (doivent être bornées)
    assert validate_delta(-0.1) == 0.0
    assert validate_delta(1.1) == 1.0
    
    # Test des erreurs
    with pytest.raises(ValueError):
        validate_delta("invalid")
    
    with pytest.raises(ValueError):
        validate_delta(None)


def test_compute_delta_ae_perfect():
    """Test δ_ae = 0 pour un cas parfait."""
    psp_before = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"}
        ],
        "edges": [
            {"src": "block1", "dst": "block2"}
        ]
    }
    
    psp_after = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"}
        ],
        "edges": [
            {"src": "block1", "dst": "block2"}
        ]
    }
    
    delta = compute_delta_ae(psp_before, psp_after)
    assert delta == 0.0  # Parfait, pas de friction


def test_compute_delta_ae_partial_failure():
    """Test δ_ae > 0 pour un échec partiel."""
    psp_before = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"},
            {"id": "block3", "kind": "theorem", "content": "C"}
        ],
        "edges": [
            {"src": "block1", "dst": "block2"},
            {"src": "block2", "dst": "block3"},
            {"src": "block1", "dst": "block3"}  # Arête supplémentaire
        ]
    }
    
    psp_after = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"},
            {"id": "block3", "kind": "theorem", "content": "C"}
        ],
        "edges": [
            {"src": "block1", "dst": "block2"},
            {"src": "block2", "dst": "block3"}
            # Arête block1->block3 supprimée
        ]
    }
    
    delta = compute_delta_ae(psp_before, psp_after)
    assert 0.0 < delta < 1.0  # Friction partielle


def test_compute_delta_ae_total_failure():
    """Test δ_ae = 1 pour un échec total."""
    psp_before = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"}
        ],
        "edges": [
            {"src": "block1", "dst": "block2"}
        ]
    }
    
    psp_after = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"}
        ],
        "edges": []  # Toutes les arêtes supprimées
    }
    
    delta = compute_delta_ae(psp_before, psp_after)
    assert delta == 1.0  # Échec total


def test_compute_delta_cegis_converged():
    """Test δ_cegis pour CEGIS convergé."""
    trace = {
        "iters": 3,
        "ok": True,
        "max_iter": 16
    }
    
    delta = compute_delta_cegis(trace)
    assert 0.0 <= delta <= 1.0  # Doit être borné
    assert delta < 1.0  # Convergé, donc pas d'échec total


def test_compute_delta_cegis_not_converged():
    """Test δ_cegis = 1 pour CEGIS non convergé."""
    trace = {
        "iters": 16,
        "ok": False,
        "max_iter": 16
    }
    
    delta = compute_delta_cegis(trace)
    assert delta == 1.0  # Non convergé, échec total


def test_compute_delta_cegis_no_iterations():
    """Test δ_cegis = 1 pour CEGIS sans itérations."""
    trace = {
        "iters": 0,
        "ok": False,
        "max_iter": 16
    }
    
    delta = compute_delta_cegis(trace)
    assert delta == 1.0  # Aucune itération, échec total


def test_compute_phase_delta():
    """Test le calcul de δ pour une phase."""
    phase_entries = [
        {
            "action": "test_action",
            "deltas": {"delta_test": 0.3, "other_metric": 0.5},
            "obligations": {"delta_obligation": "0.7"}
        },
        {
            "action": "test_action2",
            "deltas": {"delta_test": 0.4},
            "obligations": {}
        }
    ]
    
    delta = compute_phase_delta(phase_entries, "test")
    assert 0.0 <= delta <= 1.0  # Doit être borné
    # Devrait être la moyenne de 0.3, 0.7, 0.4
    expected = (0.3 + 0.7 + 0.4) / 3
    assert abs(delta - expected) < 0.001


def test_compute_phase_delta_empty():
    """Test δ = 0 pour une phase vide."""
    delta = compute_phase_delta([], "empty")
    assert delta == 0.0


def test_compute_phase_delta_no_deltas():
    """Test δ = 0 pour une phase sans δ."""
    phase_entries = [
        {
            "action": "test_action",
            "deltas": {"other_metric": 0.5},
            "obligations": {"other_obligation": "value"}
        }
    ]
    
    delta = compute_phase_delta(phase_entries, "test")
    assert delta == 0.0


def test_delta_ae_from_verification():
    """Test δ_ae basé sur les résultats de vérification."""
    from xme.metrics.delta import compute_delta_ae_from_verification
    
    psp_data = {
        "blocks": [
            {"id": "block1", "kind": "axiom", "content": "A"},
            {"id": "block2", "kind": "lemma", "content": "B"}
        ],
        "edges": [
            {"src": "block1", "dst": "block2"}
        ]
    }
    
    # Toutes les vérifications S1 réussies
    verification_results = [
        {"level": "S0", "ok": True},
        {"level": "S1", "ok": True},
        {"level": "S1", "ok": True}
    ]
    
    delta = compute_delta_ae_from_verification(psp_data, verification_results)
    assert delta == 0.0  # Toutes les vérifications S1 réussies
    
    # Certaines vérifications S1 échouées
    verification_results_fail = [
        {"level": "S0", "ok": True},
        {"level": "S1", "ok": False},
        {"level": "S1", "ok": True}
    ]
    
    delta = compute_delta_ae_from_verification(psp_data, verification_results_fail)
    assert 0.0 < delta < 1.0  # Friction partielle


def test_delta_cegis_from_result():
    """Test δ_cegis à partir d'un résultat CEGIS."""
    from xme.metrics.delta import compute_delta_cegis_from_result
    from xme.engines.cegis.types import CEGISResult
    
    # CEGIS convergé efficacement
    result = CEGISResult(candidate={"value": "10110"}, iters=2, ok=True)
    delta = compute_delta_cegis_from_result(result, max_iter=16)
    assert 0.0 <= delta < 1.0  # Convergé, donc pas d'échec total
    
    # CEGIS non convergé
    result = CEGISResult(candidate=None, iters=16, ok=False)
    delta = compute_delta_cegis_from_result(result, max_iter=16)
    assert delta == 1.0  # Non convergé, échec total
    
    # CEGIS sans itérations
    result = CEGISResult(candidate=None, iters=0, ok=False)
    delta = compute_delta_cegis_from_result(result, max_iter=16)
    assert delta == 1.0  # Aucune itération, échec total
