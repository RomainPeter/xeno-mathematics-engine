# PCAP — Proof-Carrying Actions

- Append-only JSONL with chained hashes:
  - Each action entry includes prev_hash (hash of previous action) and hash = sha256(canonical(entry without hash)).
  - RunHeader first line identifies the run (run_id, started_at).
- Merkle root:
  - Leaves = action.hash values in order; pairwise concat and sha256 up to a single root.
  - `xme pcap merkle --run artifacts/pcap/run-*.jsonl`
- Verification:
  - `xme pcap verify --run ...` checks per-entry hash and chain continuity.
- Levels: S0 (fast), S1 (pre-push), S2 (CI).

## Overview

PCAP provides a capability-based security model for mathematical proofs, ensuring that:

- Proof access is controlled through capabilities
- Proof verification is cryptographically secure
- Proof capabilities are auditable and traceable

## Core Concepts

### Capabilities

A capability is a cryptographically signed token that grants specific permissions for proof operations:

- **Proof Access**: Read access to specific proofs
- **Proof Creation**: Permission to create new proofs
- **Proof Modification**: Permission to modify existing proofs
- **Proof Verification**: Permission to verify proofs

### Capability Tokens

Each capability is represented as a signed token:

```json
{
  "capability_id": "unique-capability-id",
  "subject": "user-or-system-identifier",
  "permissions": ["read", "verify"],
  "resource": "proof-identifier",
  "expires": "2024-12-31T23:59:59Z",
  "signature": "cryptographic-signature"
}
```

### Obligations Schema

PCAP defines a minimal obligations schema (S0) with required fields:

```json
{
  "policy_id": "unique-policy-identifier",
  "invariant_id": "invariant-being-enforced",
  "result": "verification-result",
  "proof_ref": "reference-to-supporting-proof"
}
```

## PCAP Architecture

### Capability Engine

The capability engine manages all proof capabilities:

```python
class CapabilityEngine:
    def issue_capability(self, subject, permissions, resource, expires):
        """Issue a new capability token."""
        pass
    
    def verify_capability(self, token):
        """Verify a capability token."""
        pass
    
    def revoke_capability(self, capability_id):
        """Revoke a capability."""
        pass
```

### Obligation Manager

The obligation manager handles proof obligations:

```python
class ObligationManager:
    def create_obligation(self, policy_id, invariant_id, result, proof_ref):
        """Create a new obligation."""
        pass
    
    def verify_obligation(self, obligation):
        """Verify an obligation is satisfied."""
        pass
    
    def check_compliance(self, subject, resource):
        """Check compliance with obligations."""
        pass
```

## Security Model

### Cryptographic Verification

All capabilities are cryptographically signed:

```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

def sign_capability(capability, private_key):
    """Sign a capability token."""
    message = json.dumps(capability, sort_keys=True)
    signature = private_key.sign(
        message.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

def verify_capability(capability, signature, public_key):
    """Verify a capability token."""
    message = json.dumps(capability, sort_keys=True)
    try:
        public_key.verify(
            signature,
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except:
        return False
```

### Access Control

PCAP enforces fine-grained access control:

```python
class AccessController:
    def check_access(self, subject, resource, action):
        """Check if subject can perform action on resource."""
        capabilities = self.get_capabilities(subject)
        for capability in capabilities:
            if self.matches_resource(capability, resource):
                if action in capability.permissions:
                    if not self.is_expired(capability):
                        return True
        return False
```

## Obligation Schema (S0)

### Required Fields

The minimal obligation schema includes these mandatory fields:

1. **policy_id**: Unique identifier for the policy
2. **invariant_id**: Identifier for the invariant being enforced
3. **result**: The verification result
4. **proof_ref**: Reference to the supporting proof

### Schema Validation

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ObligationS0(BaseModel):
    policy_id: str = Field(..., description="Unique policy identifier")
    invariant_id: str = Field(..., description="Invariant being enforced")
    result: str = Field(..., description="Verification result")
    proof_ref: str = Field(..., description="Reference to supporting proof")
    
    class Config:
        json_schema_extra = {
            "example": {
                "policy_id": "pol-001",
                "invariant_id": "inv-001",
                "result": "verified",
                "proof_ref": "proof-123"
            }
        }
```

## Usage Examples

### Creating Capabilities

```python
from xme.pcap import CapabilityEngine, ObligationManager

# Initialize engines
cap_engine = CapabilityEngine()
obligation_mgr = ObligationManager()

# Create a capability
capability = cap_engine.issue_capability(
    subject="user123",
    permissions=["read", "verify"],
    resource="proof-456",
    expires="2024-12-31T23:59:59Z"
)

# Create an obligation
obligation = obligation_mgr.create_obligation(
    policy_id="pol-001",
    invariant_id="inv-001",
    result="verified",
    proof_ref="proof-123"
)
```

### Verifying Capabilities

```python
# Verify a capability
if cap_engine.verify_capability(token):
    print("Capability is valid")
else:
    print("Capability is invalid or expired")

# Check access
if access_controller.check_access("user123", "proof-456", "read"):
    print("Access granted")
else:
    print("Access denied")
```

## Integration with PSP

### Proof Verification

PCAP integrates with PSP for proof verification:

```python
def verify_proof_with_capability(proof, capability):
    """Verify a proof using a capability."""
    if not cap_engine.verify_capability(capability):
        raise ValueError("Invalid capability")
    
    if not access_controller.check_access(
        capability.subject, 
        proof.id, 
        "verify"
    ):
        raise ValueError("Insufficient permissions")
    
    return psp_engine.verify_proof(proof)
```

### Obligation Enforcement

```python
def enforce_obligations(proof, obligations):
    """Enforce obligations for a proof."""
    for obligation in obligations:
        if not obligation_mgr.verify_obligation(obligation):
            raise ValueError(f"Obligation {obligation.policy_id} not satisfied")
    
    return True
```

## Best Practices

### Capability Management

1. **Principle of Least Privilege**: Grant minimal necessary permissions
2. **Time-Limited Capabilities**: Use expiration dates for capabilities
3. **Regular Auditing**: Audit capability usage regularly
4. **Revocation**: Implement capability revocation mechanisms

### Security Considerations

1. **Cryptographic Strength**: Use strong cryptographic algorithms
2. **Key Management**: Secure key storage and rotation
3. **Audit Logging**: Log all capability operations
4. **Access Monitoring**: Monitor for suspicious access patterns

## Performance Optimization

### Caching

```python
class CachedCapabilityEngine(CapabilityEngine):
    def __init__(self):
        super().__init__()
        self.cache = {}
    
    def verify_capability(self, token):
        if token in self.cache:
            return self.cache[token]
        
        result = super().verify_capability(token)
        self.cache[token] = result
        return result
```

### Batch Operations

```python
def batch_verify_capabilities(tokens):
    """Verify multiple capabilities efficiently."""
    results = {}
    for token in tokens:
        results[token] = cap_engine.verify_capability(token)
    return results
```

## Troubleshooting

### Common Issues

1. **Expired Capabilities**: Check capability expiration dates
2. **Invalid Signatures**: Verify cryptographic signatures
3. **Permission Denied**: Check capability permissions
4. **Resource Mismatch**: Ensure capability matches resource

### Debugging Tools

```python
from xme.pcap import debug_capability

# Debug capability issues
debug_info = debug_capability(token)
print(debug_info.validity)
print(debug_info.permissions)
print(debug_info.expiration)
```

## Future Enhancements

### Planned Features

- **Delegation**: Capability delegation mechanisms
- **Composition**: Capability composition and inheritance
- **Revocation Lists**: Distributed capability revocation
- **Audit Trails**: Comprehensive audit logging

### Integration Points

- **Policy Engine**: Integration with policy management
- **Orchestrator**: Integration with proof orchestration
- **Persistence**: Capability storage and retrieval
- **Monitoring**: Capability usage monitoring

## References

- [PCAP Specification](pcap-spec.md) - Detailed technical specification
- [Security Model](security-model.md) - Security architecture
- [Obligation Schema](obligation-schema.md) - Obligation schema documentation
