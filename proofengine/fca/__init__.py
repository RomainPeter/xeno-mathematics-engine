"""
Formal Concept Analysis (FCA) module.
Provides Next-Closure algorithm and AEEngine implementation.
"""

from .context import FormalContext, Object, Attribute, Intent, Extent
from .next_closure import NextClosure, closure, lectic_leq
from .ae_engine import AEEngine, Concept, ConceptLattice

__all__ = [
    "FormalContext",
    "Object",
    "Attribute",
    "Intent",
    "Extent",
    "NextClosure",
    "closure",
    "lectic_leq",
    "AEEngine",
    "Concept",
    "ConceptLattice",
]
