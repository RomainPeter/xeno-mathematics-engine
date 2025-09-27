"""Collection of pure functions used in unit tests."""

from __future__ import annotations

import math
from statistics import mean, median, pstdev
from typing import List, Optional, Sequence


def calculate_fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    if n in (0, 1):
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def calculate_prime_factors(n: int) -> List[int]:
    if n <= 0:
        raise ValueError("n must be positive")
    factors: List[int] = []
    divisor = 2
    while n > 1 and divisor * divisor <= n:
        while n % divisor == 0:
            factors.append(divisor)
            n //= divisor
        divisor += 1
    if n > 1:
        factors.append(n)
    return factors


def calculate_gcd(a: int, b: int) -> int:
    return math.gcd(a, b)


def is_prime(n: int) -> bool:
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def calculate_statistics(numbers: Sequence[float]) -> tuple[float, float, float]:
    if not numbers:
        raise ValueError("numbers must not be empty")
    m = mean(numbers)
    s = pstdev(numbers)
    med = median(numbers)
    return float(m), float(s), float(med)


def merge_sorted_lists(list1: Sequence[int], list2: Sequence[int]) -> List[int]:
    result: List[int] = []
    i = j = 0
    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1
    result.extend(list1[i:])
    result.extend(list2[j:])
    return result


def binary_search(sorted_list: Sequence[int], target: int) -> Optional[int]:
    low, high = 0, len(sorted_list) - 1
    while low <= high:
        mid = (low + high) // 2
        value = sorted_list[mid]
        if value == target:
            return mid
        if value < target:
            low = mid + 1
        else:
            high = mid - 1
    return None


def quicksort(arr: Sequence[int]) -> List[int]:
    if len(arr) <= 1:
        return list(arr)
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)


def calculate_permutations(n: int, r: int) -> int:
    if n < 0 or r < 0:
        return 0
    if r > n:
        return 0
    return math.perm(n, r)


def calculate_combinations(n: int, r: int) -> int:
    if n < 0 or r < 0:
        return 0
    if r > n:
        return 0
    return math.comb(n, r)
