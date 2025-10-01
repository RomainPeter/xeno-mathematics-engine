# Methods

Proof verification methods for the Xeno Mathematics Engine.

## Overview

The methods directory contains implementations of various proof verification methods, including Automated Theorem Proving (AE), Counter-Example Guided Inductive Synthesis (CEGIS), and other mathematical proof techniques.

## Architecture

```
methods/
├── base_method.py       # Base method interface
├── ae/                  # Automated Theorem Proving
├── cegis/               # CEGIS methods
├── egraph/              # E-graph methods
├── ids/                 # IDS methods
├── hstree/              # HS-Tree methods
└── custom/              # Custom proof methods
```

## Base Method Interface

All methods implement a common interface:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum

class MethodType(Enum):
    """Types of proof methods."""
    AE = "automated_theorem_proving"
    CEGIS = "counter_example_guided_inductive_synthesis"
    EGRAPH = "e_graph"
    IDS = "ids"
    HSTREE = "hs_tree"
    CUSTOM = "custom"

class BaseMethod(ABC):
    """Base class for all proof methods."""
    
    def __init__(self, config):
        self.config = config
        self.name = self.__class__.__name__
        self.type = self._get_method_type()
    
    @abstractmethod
    def _get_method_type(self) -> MethodType:
        """Get the method type."""
        pass
    
    @abstractmethod
    def verify_proof(self, proof: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a proof using this method."""
        pass
    
    @abstractmethod
    def can_handle(self, proof_type: str) -> bool:
        """Check if this method can handle the given proof type."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get method capabilities and limitations."""
        pass
```

## Method Implementations

### Automated Theorem Proving (AE)

```python
class AEMethod(BaseMethod):
    """Automated Theorem Proving method."""
    
    def _get_method_type(self) -> MethodType:
        return MethodType.AE
    
    def verify_proof(self, proof: Dict[str, Any]) -> Dict[str, Any]:
        """Verify proof using automated theorem proving."""
        # Implement AE verification logic
        pass
    
    def can_handle(self, proof_type: str) -> bool:
        """AE can handle first-order logic proofs."""
        return proof_type in ["first_order", "propositional"]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return AE method capabilities."""
        return {
            "proof_types": ["first_order", "propositional"],
            "max_complexity": "medium",
            "timeout": 300
        }
```

### CEGIS Method

```python
class CEGISMethod(BaseMethod):
    """CEGIS method implementation."""
    
    def _get_method_type(self) -> MethodType:
        return MethodType.CEGIS
    
    def verify_proof(self, proof: Dict[str, Any]) -> Dict[str, Any]:
        """Verify proof using CEGIS method."""
        # Implement CEGIS verification logic
        pass
    
    def can_handle(self, proof_type: str) -> bool:
        """CEGIS can handle synthesis problems."""
        return proof_type in ["synthesis", "inductive"]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return CEGIS method capabilities."""
        return {
            "proof_types": ["synthesis", "inductive"],
            "max_complexity": "high",
            "timeout": 600
        }
```

## Method Registry

The method registry manages available methods:

```python
class MethodRegistry:
    """Registry for proof verification methods."""
    
    def __init__(self):
        self.methods = {}
    
    def register_method(self, name: str, method_class):
        """Register a new method."""
        self.methods[name] = method_class
    
    def get_method(self, name: str, config: Dict[str, Any]):
        """Get a method instance."""
        if name not in self.methods:
            raise ValueError(f"Unknown method: {name}")
        return self.methods[name](config)
    
    def list_methods(self) -> List[str]:
        """List all available methods."""
        return list(self.methods.keys())
```

## Development Status

This component is currently in the planning phase. The methods will be implemented in Epic 1-2 as part of the core system architecture.

## References

- [Method Design Document](method-design.md)
- [Verification Examples](verification-examples.md)
- [Performance Guide](performance-guide.md)
- [API Reference](api-reference.md)
