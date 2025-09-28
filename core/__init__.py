"""
Core components for Discovery Engine 2-Cat.
Migrated from proof-engine-for-code.
"""

from .egraph import EGraph, canonicalize_state, canonicalize_choreography
from .state import State, CognitiveState
from .journal import Journal, JournalEntry
from .canonicalization import Canonicalizer

__all__ = [
    "EGraph",
    "canonicalize_state",
    "canonicalize_choreography",
    "State",
    "CognitiveState",
    "Journal",
    "JournalEntry",
    "Canonicalizer",
]
