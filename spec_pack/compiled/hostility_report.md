# Hostility Report (A2H)
Ambition: Symbiotic AI — Mémoire probatoire (id ANF-001, v0.2)
Mission: Fournir une mémoire probatoire auditable (minimalité, traçabilité bornée) pour IA régulée.

Required:
- Obligations: ['O-1', 'O-2', 'O-4', 'O-5'] → missing vs manual: ['O-1', 'O-2', 'O-4', 'O-5']
- Invariants:  ['I-1', 'I-2', 'I-3', 'I-4', 'I-5', 'I-6', 'I-7'] → missing vs manual: ['I-1', 'I-2', 'I-3', 'I-4', 'I-5', 'I-6', 'I-7']
- Tests:       S1=False (need ['H-S1-01']), S2=False (need ['H-S2-01'])

Optional (not required to pass):
- Obligations: ['O-10', 'O-12', 'O-3', 'O-6', 'O-7', 'O-8']
- Invariants:  []
- Tests:       {'S1': [], 'S2': [], 'S3': []}

Edges (sample):
- G-1 → O-1 (minimality→obligation)
- G-1 → I-6 (minimality→invariant)
- G-2 → O-2 (journal→obligation)
- G-2 → I-7 (journal→invariant)
- G-3 → O-3 (audit24h→obligation)
- G-4 → O-4 (trace_bound→obligation)
- G-4 → I-5 (trace_bound→invariant)
- G-5 → I-1 (monotonicity→invariant)
- C-3 → O-5 (provenance→obligation)
- C-3 → I-2 (provenance→invariant)
