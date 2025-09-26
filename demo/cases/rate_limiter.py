"""
Cas de démonstration: Limitation de débit (Rate Limiting).
Objectif: Implémenter un système de limitation de débit pour les API.
"""

import time
from typing import Dict, Optional


class RateLimiter:
    """
    Limiteur de débit basé sur un bucket de tokens.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialise le limiteur de débit.
        
        Args:
            capacity: Capacité maximale du bucket
            refill_rate: Taux de remplissage (tokens par seconde)
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Consomme des tokens du bucket.
        
        Args:
            tokens: Nombre de tokens à consommer
            
        Returns:
            bool: True si les tokens ont été consommés, False sinon
        """
        self._refill_tokens()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill_tokens(self) -> None:
        """Remplit le bucket selon le taux de remplissage."""
        now = time.time()
        time_passed = now - self.last_refill
        
        # Calculer le nombre de tokens à ajouter
        tokens_to_add = time_passed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_remaining_tokens(self) -> int:
        """Retourne le nombre de tokens restants."""
        self._refill_tokens()
        return int(self.tokens)


def rate_limit_decorator(capacity: int, refill_rate: float):
    """
    Décorateur pour limiter le débit d'une fonction.
    
    Args:
        capacity: Capacité maximale du bucket
        refill_rate: Taux de remplissage (tokens par seconde)
    """
    limiter = RateLimiter(capacity, refill_rate)
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            if limiter.consume():
                return func(*args, **kwargs)
            else:
                raise Exception("Rate limit exceeded")
        return wrapper
    return decorator


@rate_limit_decorator(capacity=10, refill_rate=1.0)
def api_endpoint(data: str) -> str:
    """
    Point d'API avec limitation de débit.
    
    Args:
        data: Données à traiter
        
    Returns:
        str: Réponse de l'API
    """
    return f"Processed: {data}"


def test_rate_limiter():
    """Tests pour le limiteur de débit."""
    import pytest
    
    # Test du limiteur de base
    limiter = RateLimiter(capacity=5, refill_rate=1.0)
    
    # Consommer tous les tokens
    for _ in range(5):
        assert limiter.consume() == True
    
    # Le bucket devrait être vide
    assert limiter.consume() == False
    
    # Attendre le remplissage
    time.sleep(1.1)
    assert limiter.consume() == True
    
    # Test du décorateur
    @rate_limit_decorator(capacity=2, refill_rate=1.0)
    def test_func():
        return "success"
    
    # Premiers appels devraient réussir
    assert test_func() == "success"
    assert test_func() == "success"
    
    # Le troisième devrait échouer
    with pytest.raises(Exception, match="Rate limit exceeded"):
        test_func()


if __name__ == "__main__":
    test_rate_limiter()
    print("✅ Tests de limitation de débit réussis")
