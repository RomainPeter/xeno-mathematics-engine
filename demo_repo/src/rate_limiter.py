"""
Module de limitation de débit (Rate Limiting).
Implémente un système de limitation de débit pour les API.
"""

import time
from typing import Dict, Optional
from collections import defaultdict, deque


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


class SlidingWindowRateLimiter:
    """
    Limiteur de débit basé sur une fenêtre glissante.
    """
    
    def __init__(self, max_requests: int, window_size: float):
        """
        Initialise le limiteur avec fenêtre glissante.
        
        Args:
            max_requests: Nombre maximum de requêtes
            window_size: Taille de la fenêtre en secondes
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = deque()
    
    def is_allowed(self) -> bool:
        """
        Vérifie si une requête est autorisée.
        
        Returns:
            bool: True si la requête est autorisée
        """
        now = time.time()
        
        # Supprimer les requêtes anciennes
        while self.requests and self.requests[0] <= now - self.window_size:
            self.requests.popleft()
        
        # Vérifier si on peut ajouter une nouvelle requête
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    def get_remaining_requests(self) -> int:
        """Retourne le nombre de requêtes restantes."""
        now = time.time()
        
        # Supprimer les requêtes anciennes
        while self.requests and self.requests[0] <= now - self.window_size:
            self.requests.popleft()
        
        return max(0, self.max_requests - len(self.requests))


class RateLimitManager:
    """
    Gestionnaire de limitation de débit pour plusieurs clients.
    """
    
    def __init__(self, default_capacity: int = 100, default_refill_rate: float = 1.0):
        """
        Initialise le gestionnaire.
        
        Args:
            default_capacity: Capacité par défaut
            default_refill_rate: Taux de remplissage par défaut
        """
        self.default_capacity = default_capacity
        self.default_refill_rate = default_refill_rate
        self.limiters: Dict[str, RateLimiter] = {}
    
    def get_limiter(self, client_id: str) -> RateLimiter:
        """
        Obtient le limiteur pour un client.
        
        Args:
            client_id: Identifiant du client
            
        Returns:
            RateLimiter: Limiteur pour le client
        """
        if client_id not in self.limiters:
            self.limiters[client_id] = RateLimiter(
                self.default_capacity,
                self.default_refill_rate
            )
        
        return self.limiters[client_id]
    
    def is_allowed(self, client_id: str, tokens: int = 1) -> bool:
        """
        Vérifie si un client peut effectuer une action.
        
        Args:
            client_id: Identifiant du client
            tokens: Nombre de tokens requis
            
        Returns:
            bool: True si l'action est autorisée
        """
        limiter = self.get_limiter(client_id)
        return limiter.consume(tokens)
    
    def get_client_status(self, client_id: str) -> Dict[str, int]:
        """
        Retourne le statut d'un client.
        
        Args:
            client_id: Identifiant du client
            
        Returns:
            Dict[str, int]: Statut du client
        """
        limiter = self.get_limiter(client_id)
        return {
            "remaining_tokens": limiter.get_remaining_tokens(),
            "capacity": limiter.capacity,
            "refill_rate": limiter.refill_rate
        }
