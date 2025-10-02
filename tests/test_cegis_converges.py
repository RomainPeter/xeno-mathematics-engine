"""
Tests pour la convergence CEGIS sur des secrets de différentes longueurs.
"""
import orjson
from pathlib import Path
from xme.engines.cegis.engine import CEGISEngine
from xme.engines.cegis.domains.bitvector import BitvectorDomain


def test_cegis_converges_length_4():
    """Test que CEGIS converge en ≤ 4 itérations pour un secret de longueur 4."""
    secret = "1010"
    domain = BitvectorDomain(secret)
    engine = CEGISEngine(domain)
    
    initial_state = domain.create_initial_state()
    result = engine.run(4, initial_state)
    
    assert result.ok
    assert result.iters <= 4
    assert result.candidate["bits"] == secret


def test_cegis_converges_length_8():
    """Test que CEGIS converge en ≤ 8 itérations pour un secret de longueur 8."""
    secret = "10101100"
    domain = BitvectorDomain(secret)
    engine = CEGISEngine(domain)
    
    initial_state = domain.create_initial_state()
    result = engine.run(8, initial_state)
    
    assert result.ok
    assert result.iters <= 8
    assert result.candidate["bits"] == secret


def test_cegis_converges_deterministic():
    """Test que CEGIS produit des résultats déterministes."""
    secret = "1101"
    domain = BitvectorDomain(secret)
    engine = CEGISEngine(domain)
    
    initial_state = domain.create_initial_state()
    result1 = engine.run(4, initial_state)
    
    # Reset et re-run
    engine.reset()
    initial_state = domain.create_initial_state()
    result2 = engine.run(4, initial_state)
    
    assert result1.ok == result2.ok
    assert result1.iters == result2.iters
    assert result1.candidate == result2.candidate


def test_cegis_max_iterations():
    """Test que CEGIS respecte la limite d'itérations."""
    secret = "11111111"  # Secret long
    domain = BitvectorDomain(secret)
    engine = CEGISEngine(domain)
    
    initial_state = domain.create_initial_state()
    result = engine.run(2, initial_state)  # Limite très basse
    
    # Peut converger ou atteindre la limite
    assert result.iters <= 2
    if not result.ok:
        assert result.reason == "max_iterations_reached"
