"""
Formal Concept Analysis (FCA) module.
Provides Next-Closure algorithm and AEEngine implementation.
"""

from .ae_engine import AEEngine, Concept, ConceptLattice
from .context import Attribute, Extent, FormalContext, Intent, Object
from .next_closure import NextClosure, closure, lectic_leq

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
