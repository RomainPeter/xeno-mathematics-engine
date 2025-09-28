# Issues Post v0.1.0 - Discovery Engine 2-Cat

## 🎯 Issues à ouvrir pour les extensions post v0.1

### 1. Bench baselines et ablations
**Titre:** `feat: Comprehensive baseline benchmarking and ablation studies`
**Labels:** `enhancement`, `benchmarking`, `research`
**Description:**
- Implémenter des baselines réels (React, Tree of Thoughts, DSPy)
- Ajouter des études d'ablation complètes
- Générer des rapports HTML détaillés
- Intégrer des métriques de performance avancées

**Acceptance Criteria:**
- [ ] Baselines React, ToT, DSPy implémentés
- [ ] Ablations egraph, bandit, dpp, incident complètes
- [ ] Rapport HTML généré automatiquement
- [ ] Métriques de performance documentées

### 2. Calcul et corrélation δ
**Titre:** `feat: Delta calculation and correlation analysis`
**Labels:** `enhancement`, `metrics`, `analysis`
**Description:**
- Implémenter le calcul de δ (delta) dans `demos/run_demo.py`
- Ajouter l'analyse de corrélation entre δ et les incidents
- Intégrer les métriques de variance et de stabilité

**Acceptance Criteria:**
- [ ] Calcul de δ implémenté
- [ ] Corrélation δ-incidents calculée
- [ ] Métriques de variance documentées
- [ ] Tests de stabilité ajoutés

### 3. Docker hermétique + SBOM + release workflow
**Titre:** `feat: Hermetic Docker builds with SBOM and automated release`
**Labels:** `devops`, `security`, `release`
**Description:**
- Dockerfile hermétique avec dépendances pinées
- Génération automatique de SBOM
- Workflow de release automatisé
- Attestation Cosign intégrée

**Acceptance Criteria:**
- [ ] Dockerfile hermétique avec digest pinning
- [ ] SBOM généré automatiquement
- [ ] Workflow de release automatisé
- [ ] Attestation Cosign fonctionnelle

### 4. Documentation v0.1 (6 fichiers)
**Titre:** `docs: Complete documentation suite v0.1`
**Labels:** `documentation`, `user-guide`
**Description:**
- Quickstart Guide
- Architecture Guide
- Domain Specification Guide
- APIs Reference
- Metrics Guide
- Incident Handling Guide

**Acceptance Criteria:**
- [ ] Quickstart.md complet
- [ ] Architecture.md détaillé
- [ ] DomainSpec.md avec exemples
- [ ] APIs.md avec références
- [ ] Metrics.md avec seuils
- [ ] IncidentHandling.md avec cas d'usage

### 5. Test de déterminisme (3 runs, même Merkle)
**Titre:** `test: Determinism bounds validation`
**Labels:** `testing`, `reproducibility`
**Description:**
- Test de déterminisme avec 3 runs identiques
- Validation du Merkle root identique
- Seuils de variance V_actual ≤ 2%
- Documentation des limites de déterminisme

**Acceptance Criteria:**
- [ ] Test de déterminisme automatisé
- [ ] Merkle root identique validé
- [ ] Variance V_actual ≤ 2% vérifiée
- [ ] Limites documentées

## 🔮 Extensions futures (post v0.1)

### 6. HS-Tree pour minimiser jeux de tests
**Titre:** `feat: HS-Tree for test suite minimization`
**Labels:** `enhancement`, `optimization`, `regtech`
**Description:**
- Implémentation de HS-Tree pour la minimisation des jeux de tests
- Intégration avec le domaine RegTech/Code
- Optimisation des coûts de vérification

### 7. IDS (Information-Directed Sampling)
**Titre:** `feat: Information-Directed Sampling for expensive queries`
**Labels:** `enhancement`, `optimization`, `sampling`
**Description:**
- Implémentation d'IDS pour les requêtes coûteuses
- Optimisation des coûts d'oracle
- Intégration avec les bandits contextuels

### 8. MCTS-lite conditionnel
**Titre:** `feat: Conditional MCTS-lite for complex planning`
**Labels:** `enhancement`, `planning`, `mcts`
**Description:**
- MCTS-lite activé conditionnellement
- Déclenchement basé sur la profondeur locale > 1
- Intégration avec l'orchestrateur unifié

### 9. CVaR dans V pour profils risque
**Titre:** `feat: CVaR integration in cost vector V`
**Labels:** `enhancement`, `risk-management`, `metrics`
**Description:**
- Intégration de CVaR dans le vecteur de coût V
- Gestion des profils de risque
- Métriques de risque avancées

## 📋 Template d'Issue

```markdown
## 🎯 Objectif
[Description claire de l'objectif]

## 📋 Critères d'acceptation
- [ ] Critère 1
- [ ] Critère 2
- [ ] Critère 3

## 🔧 Implémentation
[Description technique de l'implémentation]

## 🧪 Tests
[Description des tests à ajouter]

## 📚 Documentation
[Documentation à mettre à jour]

## 🏷️ Labels
`enhancement`, `[domaine]`, `[priorité]`
```

## 🚀 Priorités

### Haute priorité (Semaine 1-2)
1. Documentation v0.1 complète
2. Test de déterminisme automatisé
3. Docker hermétique + SBOM

### Moyenne priorité (Semaine 3-4)
4. Calcul et corrélation δ
5. Bench baselines et ablations

### Basse priorité (Post v0.1)
6. HS-Tree pour minimisation
7. IDS pour requêtes coûteuses
8. MCTS-lite conditionnel
9. CVaR dans V

## 📊 Métriques de succès

- **Documentation**: 6 fichiers docs complets
- **Tests**: 100% de couverture sur les nouveaux composants
- **Performance**: Amélioration ≥ 20% vs baselines
- **Sécurité**: 0 vulnérabilités High/Critical
- **Déterminisme**: Variance ≤ 2% sur 3 runs
