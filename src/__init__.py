"""Re-export demo utilities for tests."""

from .sanitize import sanitize_input, validate_email, clean_html, escape_sql
from .rate_limiter import RateLimiter, SlidingWindowRateLimiter, RateLimitManager
from .pure_fn import (
    calculate_fibonacci,
    calculate_prime_factors,
    calculate_gcd,
    is_prime,
    calculate_statistics,
    merge_sorted_lists,
    binary_search,
    quicksort,
    calculate_permutations,
    calculate_combinations,
)
from .utils import sanitize_input as basic_sanitize_input, add

__all__ = [
    "sanitize_input",
    "validate_email",
    "clean_html",
    "escape_sql",
    "RateLimiter",
    "SlidingWindowRateLimiter",
    "RateLimitManager",
    "calculate_fibonacci",
    "calculate_prime_factors",
    "calculate_gcd",
    "is_prime",
    "calculate_statistics",
    "merge_sorted_lists",
    "binary_search",
    "quicksort",
    "calculate_permutations",
    "calculate_combinations",
    "basic_sanitize_input",
    "add",
]
