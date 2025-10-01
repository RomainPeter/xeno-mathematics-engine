# PSP (Proof Structure Protocol)

The Proof Structure Protocol (PSP) defines how mathematical proofs are structured, represented, and validated within the Xeno Mathematics Engine.

## Overview

PSP provides a standardized way to represent mathematical proofs as directed acyclic graphs (DAGs), ensuring that:

- Proof dependencies are clearly defined
- Circular dependencies are prevented
- Proof structures are verifiable and reproducible

## Core Concepts

### Proof Nodes

Each proof is represented as a node in a DAG with the following properties:

- **Node ID**: Unique identifier for the proof
- **Proof Type**: Classification of the proof method
- **Dependencies**: List of prerequisite proofs
- **Metadata**: Additional information about the proof

### DAG Validation

PSP enforces strict DAG properties:

- **Acyclicity**: No circular dependencies allowed
- **Reachability**: All dependencies must be accessible
- **Completeness**: All required dependencies must be present

### Proof Kinds

PSP supports various proof kinds through standardized enums:

```python
class ProofKind(Enum):
    AXIOM = "axiom"
    LEMMA = "lemma"
    THEOREM = "theorem"
    COROLLARY = "corollary"
    DEFINITION = "definition"
```

## PSP Schema

### Basic Structure

```json
{
  "psp_version": "1.0",
  "proof_id": "unique-proof-identifier",
  "kind": "theorem",
  "statement": "Mathematical statement to be proven",
  "dependencies": ["dep1", "dep2"],
  "proof_steps": [...],
  "metadata": {
    "author": "Author Name",
    "date": "2024-01-01",
    "context": "Mathematical context"
  }
}
```

### Validation Rules

1. **DAG Property**: The dependency graph must be acyclic
2. **Type Safety**: All proof kinds must be valid enum values
3. **Completeness**: All referenced dependencies must exist
4. **Consistency**: Proof steps must be logically consistent

## Implementation

### NetworkX Integration

PSP uses NetworkX for DAG validation:

```python
import networkx as nx

def validate_psp_dag(proofs):
    """Validate that the proof structure forms a valid DAG."""
    G = nx.DiGraph()
    
    # Add nodes and edges
    for proof in proofs:
        G.add_node(proof.id)
        for dep in proof.dependencies:
            G.add_edge(dep, proof.id)
    
    # Check for cycles
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("Proof structure contains cycles")
    
    return True
```

### Custom Constraints

PSP supports additional validation hooks:

```python
def validate_proof_constraints(proof):
    """Custom validation for specific proof constraints."""
    if proof.kind == "theorem" and not proof.dependencies:
        raise ValueError("Theorems must have dependencies")
    
    if proof.kind == "axiom" and proof.dependencies:
        raise ValueError("Axioms cannot have dependencies")
```

## Usage Examples

### Creating a Simple Proof

```python
from xme.psp import PSPProof, ProofKind

# Create a basic proof
proof = PSPProof(
    proof_id="pythagorean-theorem",
    kind=ProofKind.THEOREM,
    statement="a² + b² = c²",
    dependencies=["euclidean-geometry", "triangle-properties"],
    proof_steps=[
        "Construct right triangle",
        "Apply geometric properties",
        "Derive algebraic relationship"
    ]
)
```

### Validating Proof Structure

```python
from xme.psp import validate_psp_structure

# Validate a collection of proofs
proofs = [proof1, proof2, proof3]
try:
    validate_psp_structure(proofs)
    print("All proofs are valid")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

## Best Practices

### Proof Organization

1. **Hierarchical Structure**: Organize proofs in logical hierarchies
2. **Clear Dependencies**: Make dependencies explicit and minimal
3. **Consistent Naming**: Use consistent naming conventions
4. **Documentation**: Document proof purposes and contexts

### Performance Considerations

1. **Dependency Minimization**: Keep dependency graphs shallow
2. **Lazy Loading**: Load proofs on demand when possible
3. **Caching**: Cache validated proof structures
4. **Parallel Processing**: Validate independent proofs in parallel

## Future Enhancements

### Planned Features

- **Incremental Validation**: Validate only changed proofs
- **Proof Compression**: Optimize storage of large proof structures
- **Visualization**: Tools for visualizing proof DAGs
- **Export Formats**: Support for various proof exchange formats

### Integration Points

- **PCAP Integration**: Seamless integration with capability protocol
- **Orchestrator Support**: Integration with proof orchestration
- **Persistence Layer**: Efficient storage and retrieval
- **Policy Engine**: Integration with security policies

## Troubleshooting

### Common Issues

1. **Circular Dependencies**: Ensure no proof depends on itself
2. **Missing Dependencies**: All referenced proofs must exist
3. **Invalid Proof Kinds**: Use only supported proof kinds
4. **Schema Validation**: Ensure JSON schema compliance

### Debugging Tools

```python
from xme.psp import debug_psp_structure

# Debug proof structure issues
debug_info = debug_psp_structure(proofs)
print(debug_info.dependency_graph)
print(debug_info.validation_errors)
```

## References

- [PSP Specification](psp-spec.md) - Detailed technical specification
- [Proof Examples](proof-examples.md) - Example proof structures
- [Validation Guide](validation-guide.md) - Comprehensive validation guide
