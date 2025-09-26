"""
Module de fonctions pures.
Contient des fonctions sans effets de bord pour le traitement de données.
"""

import math
from typing import List, Tuple, Optional, Dict, Any


def calculate_fibonacci(n: int) -> int:
    """
    Calcule le n-ième nombre de Fibonacci de manière pure.
    
    Args:
        n: Position dans la suite de Fibonacci
        
    Returns:
        int: Le n-ième nombre de Fibonacci
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


def merge_sorted_lists(list1: List[int], list2: List[int]) -> List[int]:
    """
    Fusionne deux listes triées de manière pure.
    
    Args:
        list1: Première liste triée
        list2: Deuxième liste triée
        
    Returns:
        List[int]: Liste fusionnée et triée
    """
    result = []
    i, j = 0, 0
    
    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1
    
    # Ajouter les éléments restants
    result.extend(list1[i:])
    result.extend(list2[j:])
    
    return result


def binary_search(sorted_list: List[int], target: int) -> Optional[int]:
    """
    Recherche binaire dans une liste triée de manière pure.
    
    Args:
        sorted_list: Liste triée
        target: Valeur à rechercher
        
    Returns:
        Optional[int]: Index de la valeur ou None si non trouvée
    """
    left, right = 0, len(sorted_list) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if sorted_list[mid] == target:
            return mid
        elif sorted_list[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return None


def quicksort(arr: List[int]) -> List[int]:
    """
    Tri rapide de manière pure.
    
    Args:
        arr: Liste à trier
        
    Returns:
        List[int]: Liste triée
    """
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)


def calculate_permutations(n: int, r: int) -> int:
    """
    Calcule le nombre de permutations de manière pure.
    
    Args:
        n: Nombre total d'éléments
        r: Nombre d'éléments à choisir
        
    Returns:
        int: Nombre de permutations
    """
    if n < 0 or r < 0 or r > n:
        return 0
    
    result = 1
    for i in range(n, n - r, -1):
        result *= i
    
    return result


def calculate_combinations(n: int, r: int) -> int:
    """
    Calcule le nombre de combinaisons de manière pure.
    
    Args:
        n: Nombre total d'éléments
        r: Nombre d'éléments à choisir
        
    Returns:
        int: Nombre de combinaisons
    """
    if n < 0 or r < 0 or r > n:
        return 0
    
    if r > n - r:
        r = n - r
    
    result = 1
    for i in range(r):
        result = result * (n - i) // (i + 1)
    
    return result
