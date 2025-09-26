"""
Tests pour le module de fonctions pures.
"""

import pytest
from src.pure_fn import (
    calculate_fibonacci, calculate_prime_factors, calculate_gcd,
    is_prime, calculate_statistics, merge_sorted_lists,
    binary_search, quicksort, calculate_permutations, calculate_combinations
)


class TestCalculateFibonacci:
    """Tests pour la fonction calculate_fibonacci."""
    
    def test_fibonacci_basic(self):
        """Test des cas de base."""
        assert calculate_fibonacci(0) == 0
        assert calculate_fibonacci(1) == 1
        assert calculate_fibonacci(2) == 1
    
    def test_fibonacci_sequence(self):
        """Test de la séquence de Fibonacci."""
        expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
        for i, expected_value in enumerate(expected):
            assert calculate_fibonacci(i) == expected_value
    
    def test_fibonacci_negative(self):
        """Test avec un nombre négatif."""
        with pytest.raises(ValueError):
            calculate_fibonacci(-1)
    
    def test_fibonacci_large(self):
        """Test avec un nombre plus grand."""
        assert calculate_fibonacci(10) == 55
        assert calculate_fibonacci(20) == 6765


class TestCalculatePrimeFactors:
    """Tests pour la fonction calculate_prime_factors."""
    
    def test_prime_factors_basic(self):
        """Test des cas de base."""
        assert calculate_prime_factors(1) == []
        assert calculate_prime_factors(2) == [2]
        assert calculate_prime_factors(3) == [3]
    
    def test_prime_factors_composite(self):
        """Test avec des nombres composés."""
        assert calculate_prime_factors(12) == [2, 2, 3]
        assert calculate_prime_factors(15) == [3, 5]
        assert calculate_prime_factors(60) == [2, 2, 3, 5]
    
    def test_prime_factors_negative(self):
        """Test avec un nombre négatif."""
        with pytest.raises(ValueError):
            calculate_prime_factors(-1)
    
    def test_prime_factors_zero(self):
        """Test avec zéro."""
        with pytest.raises(ValueError):
            calculate_prime_factors(0)


class TestCalculateGcd:
    """Tests pour la fonction calculate_gcd."""
    
    def test_gcd_basic(self):
        """Test des cas de base."""
        assert calculate_gcd(48, 18) == 6
        assert calculate_gcd(17, 13) == 1
        assert calculate_gcd(0, 5) == 5
        assert calculate_gcd(5, 0) == 5
    
    def test_gcd_same_numbers(self):
        """Test avec les mêmes nombres."""
        assert calculate_gcd(10, 10) == 10
    
    def test_gcd_negative(self):
        """Test avec des nombres négatifs."""
        assert calculate_gcd(-48, 18) == 6
        assert calculate_gcd(48, -18) == 6
        assert calculate_gcd(-48, -18) == 6


class TestIsPrime:
    """Tests pour la fonction is_prime."""
    
    def test_prime_numbers(self):
        """Test avec des nombres premiers."""
        assert is_prime(2) == True
        assert is_prime(3) == True
        assert is_prime(17) == True
        assert is_prime(97) == True
    
    def test_composite_numbers(self):
        """Test avec des nombres composés."""
        assert is_prime(1) == False
        assert is_prime(4) == False
        assert is_prime(15) == False
        assert is_prime(100) == False
    
    def test_negative_numbers(self):
        """Test avec des nombres négatifs."""
        assert is_prime(-1) == False
        assert is_prime(-17) == False


class TestCalculateStatistics:
    """Tests pour la fonction calculate_statistics."""
    
    def test_statistics_basic(self):
        """Test des statistiques de base."""
        numbers = [1, 2, 3, 4, 5]
        mean, std_dev, median = calculate_statistics(numbers)
        
        assert mean == 3.0
        assert std_dev == pytest.approx(1.414, abs=0.01)
        assert median == 3.0
    
    def test_statistics_even_length(self):
        """Test avec une liste de longueur paire."""
        numbers = [1, 2, 3, 4]
        mean, std_dev, median = calculate_statistics(numbers)
        
        assert mean == 2.5
        assert median == 2.5
    
    def test_statistics_single_element(self):
        """Test avec un seul élément."""
        numbers = [5]
        mean, std_dev, median = calculate_statistics(numbers)
        
        assert mean == 5.0
        assert std_dev == 0.0
        assert median == 5.0
    
    def test_statistics_empty_list(self):
        """Test avec une liste vide."""
        with pytest.raises(ValueError):
            calculate_statistics([])


class TestMergeSortedLists:
    """Tests pour la fonction merge_sorted_lists."""
    
    def test_merge_basic(self):
        """Test de fusion de base."""
        list1 = [1, 3, 5]
        list2 = [2, 4, 6]
        result = merge_sorted_lists(list1, list2)
        assert result == [1, 2, 3, 4, 5, 6]
    
    def test_merge_different_lengths(self):
        """Test avec des listes de longueurs différentes."""
        list1 = [1, 3]
        list2 = [2, 4, 6, 8]
        result = merge_sorted_lists(list1, list2)
        assert result == [1, 2, 3, 4, 6, 8]
    
    def test_merge_empty_lists(self):
        """Test avec des listes vides."""
        assert merge_sorted_lists([], [1, 2, 3]) == [1, 2, 3]
        assert merge_sorted_lists([1, 2, 3], []) == [1, 2, 3]
        assert merge_sorted_lists([], []) == []


class TestBinarySearch:
    """Tests pour la fonction binary_search."""
    
    def test_binary_search_found(self):
        """Test de recherche réussie."""
        sorted_list = [1, 3, 5, 7, 9, 11, 13]
        assert binary_search(sorted_list, 5) == 2
        assert binary_search(sorted_list, 1) == 0
        assert binary_search(sorted_list, 13) == 6
    
    def test_binary_search_not_found(self):
        """Test de recherche échouée."""
        sorted_list = [1, 3, 5, 7, 9, 11, 13]
        assert binary_search(sorted_list, 4) is None
        assert binary_search(sorted_list, 0) is None
        assert binary_search(sorted_list, 15) is None
    
    def test_binary_search_empty_list(self):
        """Test avec une liste vide."""
        assert binary_search([], 5) is None


class TestQuicksort:
    """Tests pour la fonction quicksort."""
    
    def test_quicksort_basic(self):
        """Test de tri de base."""
        arr = [3, 1, 4, 1, 5, 9, 2, 6]
        result = quicksort(arr)
        assert result == [1, 1, 2, 3, 4, 5, 6, 9]
    
    def test_quicksort_empty(self):
        """Test avec une liste vide."""
        assert quicksort([]) == []
    
    def test_quicksort_single_element(self):
        """Test avec un seul élément."""
        assert quicksort([5]) == [5]
    
    def test_quicksort_already_sorted(self):
        """Test avec une liste déjà triée."""
        arr = [1, 2, 3, 4, 5]
        result = quicksort(arr)
        assert result == [1, 2, 3, 4, 5]


class TestCalculatePermutations:
    """Tests pour la fonction calculate_permutations."""
    
    def test_permutations_basic(self):
        """Test des permutations de base."""
        assert calculate_permutations(5, 3) == 60
        assert calculate_permutations(4, 2) == 12
        assert calculate_permutations(3, 3) == 6
    
    def test_permutations_edge_cases(self):
        """Test des cas limites."""
        assert calculate_permutations(5, 0) == 1
        assert calculate_permutations(0, 0) == 1
        assert calculate_permutations(5, 6) == 0
        assert calculate_permutations(-1, 2) == 0


class TestCalculateCombinations:
    """Tests pour la fonction calculate_combinations."""
    
    def test_combinations_basic(self):
        """Test des combinaisons de base."""
        assert calculate_combinations(5, 3) == 10
        assert calculate_combinations(4, 2) == 6
        assert calculate_combinations(3, 3) == 1
    
    def test_combinations_edge_cases(self):
        """Test des cas limites."""
        assert calculate_combinations(5, 0) == 1
        assert calculate_combinations(0, 0) == 1
        assert calculate_combinations(5, 6) == 0
        assert calculate_combinations(-1, 2) == 0


if __name__ == "__main__":
    pytest.main([__file__])
