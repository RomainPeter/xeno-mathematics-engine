"""
Cas de démonstration: Fonction pure.
Objectif: Implémenter une fonction pure sans effets de bord.
"""

from typing import List, Tuple, Optional
import math


def calculate_fibonacci(n: int) -> int:
    """
    Calcule le n-ième nombre de Fibonacci de manière pure.
    
    Args:
        n: Position dans la suite de Fibonacci
        
    Returns:
        int: Le n-ième nombre de Fibonacci
        
    Raises:
        ValueError: Si n est négatif
    """
    if n < 0:
        raise ValueError("n doit être positif ou nul")
    
    if n <= 1:
        return n
    
    # Calcul itératif pour éviter la récursion
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b


def calculate_prime_factors(n: int) -> List[int]:
    """
    Calcule les facteurs premiers d'un nombre de manière pure.
    
    Args:
        n: Nombre à factoriser
        
    Returns:
        List[int]: Liste des facteurs premiers
        
    Raises:
        ValueError: Si n est négatif ou nul
    """
    if n <= 0:
        raise ValueError("n doit être positif")
    
    if n == 1:
        return []
    
    factors = []
    d = 2
    
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    
    if n > 1:
        factors.append(n)
    
    return factors


def calculate_gcd(a: int, b: int) -> int:
    """
    Calcule le plus grand commun diviseur de manière pure.
    
    Args:
        a: Premier nombre
        b: Deuxième nombre
        
    Returns:
        int: Le PGCD de a et b
    """
    while b:
        a, b = b, a % b
    return abs(a)


def is_prime(n: int) -> bool:
    """
    Vérifie si un nombre est premier de manière pure.
    
    Args:
        n: Nombre à vérifier
        
    Returns:
        bool: True si n est premier, False sinon
    """
    if n < 2:
        return False
    
    if n == 2:
        return True
    
    if n % 2 == 0:
        return False
    
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    
    return True


def calculate_statistics(numbers: List[float]) -> Tuple[float, float, float]:
    """
    Calcule les statistiques de base de manière pure.
    
    Args:
        numbers: Liste de nombres
        
    Returns:
        Tuple[float, float, float]: (moyenne, écart-type, médiane)
        
    Raises:
        ValueError: Si la liste est vide
    """
    if not numbers:
        raise ValueError("La liste ne peut pas être vide")
    
    # Moyenne
    mean = sum(numbers) / len(numbers)
    
    # Écart-type
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    std_dev = math.sqrt(variance)
    
    # Médiane
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    if n % 2 == 0:
        median = (sorted_numbers[n // 2 - 1] + sorted_numbers[n // 2]) / 2
    else:
        median = sorted_numbers[n // 2]
    
    return mean, std_dev, median


def test_pure_functions():
    """Tests pour les fonctions pures."""
    import pytest
    
    # Test de Fibonacci
    assert calculate_fibonacci(0) == 0
    assert calculate_fibonacci(1) == 1
    assert calculate_fibonacci(10) == 55
    
    with pytest.raises(ValueError):
        calculate_fibonacci(-1)
    
    # Test des facteurs premiers
    assert calculate_prime_factors(12) == [2, 2, 3]
    assert calculate_prime_factors(17) == [17]
    assert calculate_prime_factors(1) == []
    
    with pytest.raises(ValueError):
        calculate_prime_factors(0)
    
    # Test du PGCD
    assert calculate_gcd(48, 18) == 6
    assert calculate_gcd(17, 13) == 1
    assert calculate_gcd(0, 5) == 5
    
    # Test de primalité
    assert is_prime(2) == True
    assert is_prime(17) == True
    assert is_prime(15) == False
    assert is_prime(1) == False
    
    # Test des statistiques
    numbers = [1, 2, 3, 4, 5]
    mean, std_dev, median = calculate_statistics(numbers)
    assert mean == 3.0
    assert std_dev == math.sqrt(2.0)
    assert median == 3.0
    
    with pytest.raises(ValueError):
        calculate_statistics([])


if __name__ == "__main__":
    test_pure_functions()
    print("✅ Tests de fonctions pures réussis")
