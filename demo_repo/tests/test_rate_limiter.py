"""
Tests pour le module de limitation de débit.
"""

import pytest
import time
from src.rate_limiter import RateLimiter, SlidingWindowRateLimiter, RateLimitManager


class TestRateLimiter:
    """Tests pour la classe RateLimiter."""
    
    def test_initial_state(self):
        """Test de l'état initial."""
        limiter = RateLimiter(capacity=5, refill_rate=1.0)
        assert limiter.capacity == 5
        assert limiter.tokens == 5
        assert limiter.refill_rate == 1.0
    
    def test_consume_tokens(self):
        """Test de consommation de tokens."""
        limiter = RateLimiter(capacity=5, refill_rate=1.0)
        
        # Consommer tous les tokens
        for _ in range(5):
            assert limiter.consume() == True
        
        # Le bucket devrait être vide
        assert limiter.consume() == False
    
    def test_refill_tokens(self):
        """Test de remplissage des tokens."""
        limiter = RateLimiter(capacity=5, refill_rate=1.0)
        
        # Consommer tous les tokens
        for _ in range(5):
            limiter.consume()
        
        # Attendre le remplissage
        time.sleep(1.1)
        assert limiter.consume() == True
    
    def test_consume_multiple_tokens(self):
        """Test de consommation de plusieurs tokens."""
        limiter = RateLimiter(capacity=10, refill_rate=1.0)
        
        # Consommer 3 tokens d'un coup
        assert limiter.consume(3) == True
        assert limiter.get_remaining_tokens() == 7
        
        # Consommer plus que disponible
        assert limiter.consume(10) == False


class TestSlidingWindowRateLimiter:
    """Tests pour la classe SlidingWindowRateLimiter."""
    
    def test_initial_state(self):
        """Test de l'état initial."""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_size=1.0)
        assert limiter.max_requests == 5
        assert limiter.window_size == 1.0
        assert len(limiter.requests) == 0
    
    def test_allow_requests(self):
        """Test d'autorisation de requêtes."""
        limiter = SlidingWindowRateLimiter(max_requests=3, window_size=1.0)
        
        # Les 3 premières requêtes devraient être autorisées
        for _ in range(3):
            assert limiter.is_allowed() == True
        
        # La 4ème devrait être refusée
        assert limiter.is_allowed() == False
    
    def test_window_sliding(self):
        """Test du glissement de fenêtre."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_size=0.5)
        
        # Faire 2 requêtes
        assert limiter.is_allowed() == True
        assert limiter.is_allowed() == True
        
        # La 3ème devrait être refusée
        assert limiter.is_allowed() == False
        
        # Attendre que la fenêtre glisse
        time.sleep(0.6)
        assert limiter.is_allowed() == True
    
    def test_remaining_requests(self):
        """Test du calcul des requêtes restantes."""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_size=1.0)
        
        # Faire 2 requêtes
        limiter.is_allowed()
        limiter.is_allowed()
        
        assert limiter.get_remaining_requests() == 3


class TestRateLimitManager:
    """Tests pour la classe RateLimitManager."""
    
    def test_initial_state(self):
        """Test de l'état initial."""
        manager = RateLimitManager()
        assert manager.default_capacity == 100
        assert manager.default_refill_rate == 1.0
        assert len(manager.limiters) == 0
    
    def test_get_limiter(self):
        """Test d'obtention d'un limiteur."""
        manager = RateLimitManager()
        
        # Obtenir un limiteur pour un client
        limiter = manager.get_limiter("client1")
        assert isinstance(limiter, RateLimiter)
        assert limiter.capacity == 100
        
        # Le même client devrait avoir le même limiteur
        limiter2 = manager.get_limiter("client1")
        assert limiter is limiter2
    
    def test_is_allowed(self):
        """Test d'autorisation d'actions."""
        manager = RateLimitManager(default_capacity=2, default_refill_rate=1.0)
        
        # Les 2 premières actions devraient être autorisées
        assert manager.is_allowed("client1") == True
        assert manager.is_allowed("client1") == True
        
        # La 3ème devrait être refusée
        assert manager.is_allowed("client1") == False
    
    def test_client_status(self):
        """Test du statut d'un client."""
        manager = RateLimitManager(default_capacity=5, default_refill_rate=1.0)
        
        # Faire une action
        manager.is_allowed("client1")
        
        status = manager.get_client_status("client1")
        assert status["remaining_tokens"] == 4
        assert status["capacity"] == 5
        assert status["refill_rate"] == 1.0


class TestIntegration:
    """Tests d'intégration."""
    
    def test_rate_limiter_integration(self):
        """Test d'intégration du limiteur de débit."""
        limiter = RateLimiter(capacity=3, refill_rate=1.0)
        
        # Simuler des requêtes
        requests = []
        for i in range(5):
            allowed = limiter.consume()
            requests.append(allowed)
            time.sleep(0.1)
        
        # Vérifier que seules les 3 premières sont autorisées
        assert requests[:3] == [True, True, True]
        assert requests[3:] == [False, False]
    
    def test_sliding_window_integration(self):
        """Test d'intégration de la fenêtre glissante."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_size=0.5)
        
        # Simuler des requêtes
        requests = []
        for i in range(4):
            allowed = limiter.is_allowed()
            requests.append(allowed)
            time.sleep(0.1)
        
        # Vérifier que seules les 2 premières sont autorisées
        assert requests[:2] == [True, True]
        assert requests[2:] == [False, False]


if __name__ == "__main__":
    pytest.main([__file__])
