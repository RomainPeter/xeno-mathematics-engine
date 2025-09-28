# Architecture Unifiée v0.1

## Vue d'ensemble

L'Architecture Unifiée v0.1 implémente un système de preuve hybride combinant **Attribute Exploration (AE)** et **CEGIS (Counter-Example Guided Inductive Synthesis)** pour maximiser la couverture et minimiser la redondance sous contraintes K.

## Principes fondamentaux

### 1. Épine dorsale: Attribute Exploration (AE)
- **Objectif**: Garantir non-redondance et complétude minimale
- **Processus**: Boucle requête → oracle → contre-exemple
- **Algorithme**: next-closure pour exploration systématique

### 2. Synthèse: CEGIS
- **Objectif**: "Programmer" des chorégraphies qui maximisent les gains
- **Métriques**: Couverture, MDL (Minimum Description Length)
- **Contraintes**: Respect des obligations K

### 3. Anti-redondance structurelle: E-graphs
- **Fonction**: Canonicaliser états/chorégraphies et compresser J
- **Règles**: Idempotence + commutations gardées
- **Sécurité**: Toutes les équivalences sont prouvées

### 4. Rôle du LLM
- **Position**: Générateur créatif faillible
- **Contrôle**: Sous supervision AE/CEGIS + Verifier
- **Micro-prompts**: Implications, contre-exemples, variantes

## Sémantique formelle (2-cat pragmatique)

### Objets
- **X = {H, E, K, J, A, Σ}**: État cognitif typé
  - H: Hypothèses
  - E: Évidence  
  - K: Contraintes
  - J: Journal
  - A: Artéfacts
  - Σ: Seeds/Environnement

### 1-morphismes (Opérateurs)
- **∧ Meet**: Combinaison de contraintes
- **↑ Generalize**: Généralisation de patterns
- **↓ Specialize**: Spécialisation pour cas spécifiques
- **Δ Contrast**: Recherche de différences
- **⊥ Refute**: Réfutation de claims invalides
- **□ Normalize**: Canonicalisation de représentations
- **№ Verify**: Vérification de propriétés
- **⟂ Abduce**: Génération d'hypothèses

### 2-morphismes (Raffinements)
- **π ⇒ π'**: Justifiés par (V, S, K)
- **Domination**: V(π') ≤ V(π) et S(π') ≥ S(π) sur au moins une dimension
- **Enrichissement V**: Quantale (R_+^n, ≤×, ⊗=+, 0)
- **Scores S**: Vecteur (info_gain, coverage_gain, MDL_drop, novelty)

## Équations opératoires (E-graphs)

### Idempotence
- **□∘□ = □**: Normalize est idempotent
- **№∘№ = №**: Verify est idempotent après validation
- **∧∘∧ = ∧**: Meet est idempotent sur même base

### Commutation sous garde
- **Retrieve∘□ ≡ □∘Retrieve**: Si K fixe
- **∧ associative/commutative**: Si K fixe

### Absorptions utiles
- **№ après preuve validée**: Absorbante localement
- **Journal J**: Stocke témoins d'équivalence

## Interfaces de base

### X (État cognitif)
```json
{
  "id": "state_id",
  "H": [...],  // Hypothèses
  "E": [...],  // Évidence
  "K": [...],  // Contraintes
  "A": [...],  // Artéfacts
  "J": {...}, // Journal
  "Sigma": {...} // Seeds/Environnement
}
```

### DCA (Decision Context Artifact)
```json
{
  "id": "dca_id",
  "type": "AE_query|CEGIS_prog",
  "context_hash": "hash_of_X_subset",
  "query_or_prog": "A ⇒ B",
  "V_hat": {...}, "S_hat": {...},
  "V_actual": {...}, "S_actual": {...},
  "verdict": "accept|reject",
  "counterexample_ref": "...",
  "egraph_class": "canonical_class"
}
```

### PCAP (Proof-Carrying Action)
```json
{
  "id": "pcap_id",
  "action": {"name": "op", "params": {...}},
  "obligations": ["K1", "K2"],
  "context_hash": "state_snapshot",
  "proofs": [...],
  "verifier_attestation": {...},
  "costs": {"time_ms": 100, "audit_cost": 50}
}
```

### CompositeOp/Choreo
```json
{
  "id": "choreo_id",
  "ops": ["Meet", "Verify", "Normalize"],
  "pre": {...}, "post": {...},
  "guards": ["K1", "K2"],
  "budgets": {...},
  "diversity_keys": [...],
  "rationale": "explanation"
}
```

### DomainSpec (Adapter)
```json
{
  "id": "domain_spec_id",
  "domain": "RegTech|Code|Math|Finance|Healthcare",
  "closure": "exact|prob|defeasible",
  "oracle_endpoints": [...],
  "cost_model": {...},
  "admissible_equations": [...],
  "evidence_types": [...],
  "shock_ladder": {...},
  "risk_policy": {...}
}
```

## Boucles de contrôle

### AE (next-closure)
1. **Proposer implication A ⇒ B** (LLM + cache)
2. **Oracle (Verifier)**: Valid → ajouter à base (J + DCA acceptée)
3. **Contre-exemple**: Fournir c (PCAP), ajouter à E et K↑ tests
4. **Continuer** jusqu'à base fermée sous budget V

### CEGIS (chorégraphies)
1. **Synthétiser programme p**: X→X promettant ΔS≥τ et respectant K
2. **Verify**: Exécuter p en runner hermétique + tests
3. **Si fail**: Générer contre-exemple t, enrichir K, resserrer espace
4. **Accepter**: Journaliser PCAP/DCA + e-class canonique

## Politique d'exploration

### Génération d'options
- **LLM micro-prompts** → k chorégraphies/implications candidates
- **Seeds diversifiés** pour éviter la convergence prématurée

### Diversité
- **DPP/submodularité** sur clés de diversité
- **Élimination de doublons** par e-graph
- **Clés**: attributs, implications, motifs d'opérateurs

### Sélection
- **Bandit contextuel** (LinUCB/TS) sur S_hat avec coût V
- **MCTS-lite** si arbre local nécessite approfondissement
- **Budgets intégrés** via V

## Antifragilité opérationnelle

### Incident→Règle
- **Toute rejection** → FailReason → transformation
- **K↑**: OPA/e-rule/test HS-Tree
- **Cache/closure**: Ajout automatique
- **Replanification**: Guidée par incidents

### Gouvernance de stochasticité
- **Seeds, temp, model_id, prompt_hash**
- **Attestation**: cosign/in-toto dans PCAP/DCA
- **Reproductibilité**: Runner hermétique, artefacts signés

## Critères d'acceptation

### Correctness
- **Fermetures AE**: Cohérentes
- **CEGIS**: Réduit l'espace (tests/obligations ajoutés)
- **E-graph**: Aucune équivalence non sûre

### Mesure
- **S_actual** dépasse baseline (ReAct/ToT)
- **Couverture/MDL** à coût V comparable
- **δ** corrèle aux incidents/audit

### Repro
- **Runner hermétique**
- **Artefacts signés**
- **1-click repro**

## Instanciation RegTech/Code

### DomainSpec.v1
```json
{
  "domain": "RegTech",
  "closure": "exact",
  "oracle_endpoints": [
    {"type": "OPA", "endpoint": "http://localhost:8181/v1/data"},
    {"type": "static_analysis", "endpoint": "local://tools/static_analysis"},
    {"type": "property_test", "endpoint": "local://tools/hypothesis"}
  ],
  "cost_model": {
    "dimensions": ["time_ms", "audit_cost", "legal_risk", "tech_debt"]
  },
  "admissible_equations": [
    {"name": "idempotence_normalize", "rule": "□∘□ = □"},
    {"name": "idempotence_verify", "rule": "№∘№ = №"},
    {"name": "commutation_retrieve_normalize", "rule": "Retrieve∘□ ≡ □∘Retrieve"}
  ]
}
```

## Utilisation

### Démarrage rapide
```bash
# Installer les dépendances
pip install -r requirements.lock

# Lancer la démo
python scripts/demo_unified_architecture.py
```

### Configuration
```python
from proofengine.orchestrator.unified_orchestrator import UnifiedOrchestrator, ExplorationConfig

config = ExplorationConfig(
    domain_spec=domain_spec,
    budget={"time_ms": 30000, "audit_cost": 1000},
    selection_strategy="bandit",
    max_iterations=5
)

orchestrator = UnifiedOrchestrator(config)
results = await orchestrator.explore(initial_state)
```

## Prochaines étapes

1. **Intégration réelle**: Connecter aux vrais oracles OPA/static analysis
2. **Scaling**: Optimiser pour de plus grands espaces d'exploration
3. **Domaines multiples**: Étendre au-delà de RegTech/Code
4. **Métriques avancées**: Implémenter des mesures de performance plus sophistiquées
5. **Interface utilisateur**: Créer une interface pour l'exploration interactive

## Références

- [Spec Pack v0.1.1](./spec_pack/)
- [Schémas JSON](./specs/v0.1/)
- [Exemples](./examples/v0.1/)
- [Tests](./tests/)

