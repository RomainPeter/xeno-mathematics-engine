# Discovery Engine 2-Cat - Architecture Guide

## 🏗️ Unified Architecture v0.1

### Core Principles

The Discovery Engine 2-Cat implements a **2-categorical architecture** for automated discovery with the following key principles:

1. **Non-redundancy**: Structural anti-redundancy through e-graph canonicalization
2. **Minimal completeness**: Attribute Exploration (AE) with Next-Closure algorithm
3. **Antifragility**: Incident → Rule transformation with guided replanning
4. **Auditability**: Append-only signed journal with Merkle hashing

### Architectural Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Discovery Engine 2-Cat                  │
├─────────────────────────────────────────────────────────────┤
│  Orchestrator (AE + CEGIS Loops)                           │
│  ├── AE Next-Closure                                       │
│  ├── CEGIS Choreography Synthesis                          │
│  └── Unified State Management                              │
├─────────────────────────────────────────────────────────────┤
│  Methods Layer                                              │
│  ├── E-graph Canonicalization                              │
│  ├── Prompt Governance (Contract++)                       │
│  └── Policy Selection (Bandit + DPP)                       │
├─────────────────────────────────────────────────────────────┤
│  Core Layer                                                │
│  ├── Cognitive State (H, E, K, A, J, Σ)                   │
│  ├── Journal (Merkle)                                      │
│  └── Domain Adapters                                       │
├─────────────────────────────────────────────────────────────┤
│  Verification Layer                                         │
│  ├── OPA (Rego Policies)                                   │
│  ├── Static Analysis                                        │
│  └── Incident Handlers                                     │
└─────────────────────────────────────────────────────────────┘
```

## 🧠 Cognitive State (X)

The cognitive state `X = {H, E, K, J, A, Σ}` represents the complete knowledge state:

### Components

- **H (Hypotheses)**: Valid implications discovered through AE
- **E (Counter-examples)**: Refuted implications with evidence
- **K (Knowledge)**: Rules and tests derived from incidents
- **J (Journal)**: Append-only Merkle-hashed audit trail
- **A (Attributes)**: Domain-specific attributes and properties
- **Σ (Signature)**: Attestation and verification data

### State Transitions

```
Initial State → AE Loop → CEGIS Loop → Final State
     ↓              ↓           ↓           ↓
   Empty H      Propose    Synthesize   Complete
   Empty E      Verify     Choreography Knowledge
   Empty K     Incorporate Validate     Base
```

## 🔍 Attribute Exploration (AE)

### Next-Closure Algorithm

The AE loop implements the Next-Closure algorithm for minimal completeness:

```python
def ae_loop(state: XState, oracle: Oracle, budgets: Dict, thresholds: Dict):
    while not is_closed(state) and budgets_not_exhausted(budgets):
        # 1. Propose implications
        implications = propose_implications(state, k=8)
        
        # 2. Canonicalize with e-graph
        canonical_implications = canonicalize(implications)
        
        # 3. Select diverse subset
        selected = dpp_select(canonical_implications, k=3)
        
        # 4. Verify with oracle
        for impl in selected:
            result = oracle.verify_implication(impl)
            
            if result.valid:
                incorporate_valid(impl)
            else:
                incorporate_counterexample(impl, result.counterexample)
```

### Oracle Integration

The oracle provides verification through multiple backends:

- **OPA**: Rego policy evaluation
- **Static Analysis**: Code analysis tools
- **Custom Verifiers**: Domain-specific validation

## 🔗 E-graph Canonicalization

### Rules v0.1

The e-graph implements safe canonicalization rules:

```python
RULES = [
    # Idempotence
    EquivalenceRule("Normalize∘Normalize", "Normalize", "same_K"),
    EquivalenceRule("Verify∘Verify", "Verify", "same_K"),
    EquivalenceRule("Meet∘Meet", "Meet", "same_K"),
    
    # Guarded Commutation
    EquivalenceRule("Normalize∘Retrieve", "Retrieve∘Normalize", "pre_post_conditions"),
    EquivalenceRule("Verify∘Normalize", "Normalize∘Verify", "pre_post_conditions"),
    
    # Associativity/Commutativity
    EquivalenceRule("Meet_assoc", "Meet(Meet(a,b),c)", "Meet(a,Meet(b,c))"),
    EquivalenceRule("Meet_comm", "Meet(a,b)", "Meet(b,a)"),
    
    # Absorption
    EquivalenceRule("Verify_absorb", "Verify∘Verify", "Verify")
]
```

### Canonicalization Process

1. **Equivalence Detection**: Find structurally equivalent expressions
2. **Witness Generation**: Create equivalence proofs
3. **Representative Selection**: Choose canonical representatives
4. **Journal Update**: Record witnesses in Merkle journal

## 🎭 Prompt Governance

### PromptContract++

Structured prompt templates with validation:

```json
{
  "goal": "propose_implications",
  "k": 8,
  "diversity_keys": ["attributes", "clause_type"],
  "hard_constraints": ["must respect obligations K"],
  "output_contract": {
    "fields": ["premises", "conclusion", "justification", "diversity_key"]
  }
}
```

### Micro-prompts

- **AE Implications**: Generate diverse implications
- **AE Counter-examples**: Generate refuting examples
- **CEGIS Choreographies**: Synthesize operation sequences

## 🎯 Policy Selection

### Contextual Bandit (LinUCB)

```python
class LinUCB:
    def select(self, candidates: List, context: Dict) -> List:
        # Upper confidence bound selection
        scores = []
        for candidate in candidates:
            score = self.alpha * np.sqrt(
                candidate.features.T @ self.A_inv @ candidate.features
            )
            scores.append(score)
        return select_top_k(candidates, scores, k=3)
    
    def update(self, candidate, reward: float, cost: float):
        # Update bandit parameters
        self.A += candidate.features @ candidate.features.T
        self.b += reward * candidate.features
        self.A_inv = np.linalg.inv(self.A)
```

### DPP Diversity

```python
def dpp_select(candidates: List, keys: List[str], k: int, lambda_: float) -> List:
    # Determinantal Point Process for diversity
    similarity_matrix = compute_similarity(candidates, keys)
    kernel_matrix = np.exp(-lambda_ * similarity_matrix)
    
    # DPP sampling
    selected = dpp_sample(kernel_matrix, k)
    return [candidates[i] for i in selected]
```

## 🔧 Incident Handling

### FailReason Mapping

```python
INCIDENT_HANDLERS = {
    "LowNovelty": handle_low_novelty,      # → e-graph forbidden equivalence
    "LowCoverage": handle_low_coverage,     # → K target + Meet/Generalize priority
    "ConstraintBreach": handle_constraint,  # → OPA rule + e-graph block
    "OracleTimeout": handle_timeout,        # → budget increase or quarantine
    "FlakyOracle": handle_flaky            # → retry or quarantine
}
```

### Handler Actions

1. **LowNovelty**: Add forbidden equivalence to e-graph
2. **LowCoverage**: Add target to K, prioritize Meet/Generalize
3. **ConstraintBreach**: Add OPA rule, block faulty e-graph path
4. **OracleTimeout**: Increase budget or quarantine seeds
5. **FlakyOracle**: Retry with different parameters or quarantine

## 📊 Metrics and Monitoring

### Cost Vector V

The cost vector `V = [time_ms, audit_cost, legal_risk, tech_debt, novelty, coverage]` provides unified measurement:

- **time_ms**: Execution time in milliseconds
- **audit_cost**: Verification cost in USD
- **legal_risk**: Risk score (0-1)
- **tech_debt**: Technical debt score (0-1)
- **novelty**: Diversity score (0-1)
- **coverage**: Coverage gain (0-1)

### Quantale Structure

The cost vector forms a quantale `(R_+^n, ≤×, ⊗=+, 0)`:

- **Ordering**: Pareto dominance `V₁ ≤ V₂` iff `∀i: V₁ᵢ ≤ V₂ᵢ`
- **Monoidal**: Parallel composition `V₁ ⊗ V₂ = V₁ + V₂`
- **Zero**: Neutral element `0 = [0, 0, 0, 0, 0, 0]`

## 🔒 Security and Auditability

### Merkle Journal

The journal `J` provides cryptographic auditability:

```python
class Journal:
    def append(self, entry: Dict) -> str:
        # Calculate Merkle hash
        entry_hash = self._calculate_hash(entry)
        entry["merkle_parent"] = self.merkle_root
        entry["merkle_curr"] = entry_hash
        
        # Update journal
        self.entries.append(entry)
        self.merkle_root = entry_hash
        
        return entry_hash
```

### Attestation

- **Cosign**: Cryptographic signatures
- **SBOM**: Software Bill of Materials
- **Vulnerability Scanning**: Grype security analysis

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
USER discovery
CMD ["python", "scripts/demo_discovery_engine.py"]
```

### CI/CD Pipeline

1. **Build**: Docker image with pinned dependencies
2. **Test**: Comprehensive test suite
3. **Security**: SBOM generation and vulnerability scanning
4. **Attestation**: Cosign signing and verification
5. **Release**: Automated release with artifacts

## 📈 Performance Characteristics

### Complexity

- **AE Loop**: O(n²) where n is the number of attributes
- **E-graph Canonicalization**: O(n²) for equivalence detection
- **Bandit Selection**: O(d²) where d is the feature dimension
- **DPP Diversity**: O(k³) where k is the selection size

### Scalability

- **Memory**: Linear in journal size
- **CPU**: Quadratic in attribute count
- **I/O**: Minimal (oracle calls only)

## 🔮 Future Extensions

### Planned Features

1. **HS-Tree**: Minimize test suites for RegTech
2. **IDS**: Information-Directed Sampling for expensive queries
3. **MCTS-lite**: Monte Carlo Tree Search for complex planning
4. **CVaR**: Conditional Value at Risk for risk profiles

### Research Directions

- **Categorical Semantics**: Formal 2-category theory
- **Quantum Computing**: Quantum advantage for optimization
- **Federated Learning**: Distributed discovery across domains
