"""
Utility functions for demo.
"""

def sanitize_input(s: str) -> str:
    """Return a safe representation: strip and collapse spaces."""
    if s is None:
        return ""
    return " ".join(s.strip().split())

def add(a: int, b: int) -> int:
    """Pure addition."""
    return a + b
