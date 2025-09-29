# 🔍 Domain CEGIS - Code Compliance

## 📋 Vue d'ensemble

Implémentation complète du système CEGIS (Counter-Example Guided Inductive Synthesis) pour la conformité du code, avec convergence < 5 itérations, émission PCAP, et exécution concurrente.

## 🏗️ Architecture

### **Types de Base**
- **`Candidate`** : Solution candidate avec patch, spec, rationale, seed
- **`Verdict`** : Verdict de vérification avec preuves
- **`Counterexample`** : Contre-exemple avec localisation et règle
- **`ComplianceResult`** : Résultat de vérification de conformité

### **Moteurs CEGIS**
- **`CEGISEngine`** : Moteur principal CEGIS
- **`ProposalEngine`** : Moteur de proposition de candidats
- **`ComplianceVerifier`** : Vérificateur de conformité
- **`RefinementEngine`** : Moteur de raffinement

### **Règles de Conformité**
- **`DeprecatedAPIRule`** : Détection d'APIs dépréciées
- **`NamingConventionRule`** : Conventions de nommage
- **`SecurityRule`** : Vulnérabilités de sécurité
- **`CodeStyleRule`** : Style de code

## 🎯 Fonctionnalités

### **Algorithme CEGIS**
- ✅ **Convergence** : < 5 itérations sur repo jouet
- ✅ **Concurrence** : propose et verify en tâches distinctes
- ✅ **PCAP** : Émission à chaque itération
- ✅ **Modes** : stub-only (déterministe), hybrid (LLM mockable)
- ✅ **Performance** : < 100ms par itération

### **Types de Violations**
- ✅ **APIs dépréciées** : `foo_v1()`, `bar_v1()`, `baz_v1()`
- ✅ **Conventions de nommage** : PascalCase → snake_case
- ✅ **Sécurité** : `eval()` → `ast.literal_eval()`
- ✅ **Style de code** : lignes trop longues, espaces en fin

### **Modes d'Exécution**
- ✅ **Stub-only** : Mode déterministe pour tests
- ✅ **Hybrid** : Mode LLM mockable
- ✅ **Full-LLM** : Mode LLM complet

### **Tests de Convergence**
- ✅ **Repo jouet** : Violations intentionnelles
- ✅ **Convergence** : < 5 itérations
- ✅ **PCAP** : Émission à chaque itération
- ✅ **Performance** : < 100ms par itération

## 🚀 Utilisation

### **Installation**

```bash
# Installer les dépendances
make -f Makefile.domain install

# Configuration de l'environnement
export DOMAIN_CONFIG="config.yaml"
```

### **Démonstration**

```bash
# Démonstration complète
make -f Makefile.domain demo

# Démonstration rapide
make -f Makefile.domain demo-quick

# Démonstration concurrente
make -f Makefile.domain demo-concurrent

# Benchmark de performance
make -f Makefile.domain benchmark
```

### **Tests**

```bash
# Tests complets
make -f Makefile.domain test

# Tests spécifiques
make -f Makefile.domain test-convergence
make -f Makefile.domain test-modes
make -f Makefile.domain test-performance

# Tests avec couverture
make -f Makefile.domain test-coverage
```

### **Validation**

```bash
# Validation complète
make -f Makefile.domain validate

# Linting et formatage
make -f Makefile.domain lint
make -f Makefile.domain format
```

## 📊 Configuration

### **Configuration CEGIS**

```python
from proofengine.domain.cegis_engine import CEGISConfig, CEGISMode

config = CEGISConfig(
    max_iterations=5,
    timeout_per_iteration=30.0,
    mode=CEGISMode.STUB_ONLY,
    enable_concurrency=True,
    enable_pcap_emission=True,
    convergence_threshold=0.95
)
```

### **Exécution CEGIS**

```python
from proofengine.domain.cegis_engine import CEGISEngine
from proofengine.domain.types import CodeSnippet

# Créer le moteur
engine = CEGISEngine(config)

# Exécuter CEGIS
result = await engine.execute_cegis(
    code_snippet=CodeSnippet(content="result = foo_v1('input')", language="python"),
    violation_type="deprecated_api",
    rule_id="deprecated_api",
    seed="test_seed"
)

# Vérifier la convergence
assert result.iterations <= 5
assert result.success
assert result.is_converged
```

### **Modes d'Exécution**

```python
# Mode déterministe
config = CEGISConfig(mode=CEGISMode.STUB_ONLY)

# Mode hybride
config = CEGISConfig(mode=CEGISMode.HYBRID)

# Mode LLM complet
config = CEGISConfig(mode=CEGISMode.FULL_LLM)
```

## 🧪 Tests

### **Tests de Convergence**

```python
# Test convergence < 5 itérations
@pytest.mark.asyncio
async def test_convergence():
    result = await engine.execute_cegis(...)
    assert result.iterations <= 5
    assert result.success
    assert result.is_converged
```

### **Tests de Modes**

```python
# Test mode déterministe
@pytest.mark.asyncio
async def test_deterministic_mode():
    config = CEGISConfig(mode=CEGISMode.STUB_ONLY)
    engine = CEGISEngine(config)
    # ... test execution
```

### **Tests de Performance**

```python
# Test performance < 100ms
@pytest.mark.asyncio
async def test_performance():
    start_time = time.time()
    result = await engine.execute_cegis(...)
    execution_time = time.time() - start_time
    assert execution_time < 0.1  # < 100ms
```

### **Tests Concurrents**

```python
# Test exécution concurrente
@pytest.mark.asyncio
async def test_concurrent_execution():
    tasks = [engine.execute_cegis(...) for _ in range(3)]
    results = await asyncio.gather(*tasks)
    for result in results:
        assert result.success
```

## 📁 Structure des Fichiers

```
proofengine/domain/
├── __init__.py              # Module domain
├── types.py                 # Types de base
├── rules.py                 # Règles de conformité
├── proposer.py              # Moteur de proposition
├── verifier.py              # Vérificateur de conformité
├── refiner.py               # Moteur de raffinement
└── cegis_engine.py          # Moteur CEGIS principal

fixtures/toy_repo/
├── __init__.py              # Repo jouet
├── violations.py            # Violations intentionnelles
├── compliant.py             # Code conforme
└── README.md                # Documentation

tests/
└── test_domain_convergence.py  # Tests de convergence

demo_domain_cegis.py         # Démonstration
Makefile.domain              # Makefile
README_DOMAIN.md             # Documentation
```

## 🎯 Critères d'Acceptation

### **Fonctionnels**
- [x] Convergence sur repo jouet avec PCAP émis à chaque itération
- [x] Arrêt par condition de succès ou max_iters_reached
- [x] Convergence < N=5 itérations
- [x] Modes: stub-only (déterministe), hybrid (LLM mockable)

### **Techniques**
- [x] Types: Candidate{patch/spec, rationale, seed}
- [x] Types: Verdict{ok, proofs[]}|Counterexample{file,line,snippet,rule}
- [x] propose(): LLMAdapter micro-prompt déterministe (seed) -> Candidate
- [x] verify(): Verifier statique (LibCST/regex) + unit test généré -> Verdict|CE
- [x] refine(): utilise CE pour spécialiser la contrainte ou éditer le patch

### **Tests**
- [x] Fixture repo jouet: un CE trouvé puis convergence < N=5 itérations
- [x] Modes: stub-only (déterministe), hybrid (LLM mockable)
- [x] Concurrence: propose et verify en tâches distinctes selon mode
- [x] Performance: < 100ms par itération

## 📊 Résultats Attendus

### **Convergence**
- **APIs dépréciées** : 2-3 itérations
- **Conventions de nommage** : 2-3 itérations
- **Sécurité** : 2-3 itérations
- **Style de code** : 1-2 itérations
- **Violations mixtes** : 3-5 itérations

### **Performance**
- **Temps d'exécution** : < 100ms par itération
- **Convergence totale** : < 500ms
- **Exécution concurrente** : < 1s pour 3 tâches
- **Benchmark** : < 2s pour tous les cas de test

### **PCAP Émission**
- **Itérations** : 1 PCAP par itération
- **Statut** : "iteration" ou "converged"
- **Métadonnées** : candidate_id, rule_id, violation_type
- **Corrélation** : IDs de corrélation pour traçabilité

## 🔗 Intégration

### **Avec Orchestrator v1**
- ✅ **CEGIS Engine** : Intégration avec moteur CEGIS
- ✅ **PCAP Emission** : Émission PCAP à chaque itération
- ✅ **Event Bus** : Événements de convergence
- ✅ **Performance** : Optimisations pour production

### **Avec Event Bus**
- ✅ **Événements** : Génération d'événements CEGIS
- ✅ **Corrélation** : IDs de corrélation
- ✅ **Métadonnées** : Informations de convergence
- ✅ **Télémétrie** : Statistiques en temps réel

## 📝 Notes d'Implémentation

### **Optimisations**
- ✅ **Concurrence** : propose et verify en parallèle
- ✅ **Cache** : Mise en cache des résultats
- ✅ **Mémoire** : Gestion efficace de la mémoire
- ✅ **Performance** : Optimisations algorithmiques

### **Robustesse**
- ✅ **Gestion d'erreurs** : Gestion des erreurs
- ✅ **Validation** : Validation des entrées
- ✅ **Tests** : Couverture de tests complète
- ✅ **Documentation** : Documentation complète

## 🎉 Conclusion

L'implémentation Domain CEGIS est **complète et opérationnelle** avec :

- ✅ **Algorithme CEGIS** avec convergence < 5 itérations
- ✅ **Types complets** pour candidats, verdicts, contre-exemples
- ✅ **Moteurs** : propose, verify, refine
- ✅ **Tests de convergence** sur repo jouet
- ✅ **Modes d'exécution** : stub-only, hybrid
- ✅ **PCAP émission** à chaque itération
- ✅ **Performance** < 100ms par itération
- ✅ **Démonstration** complète

**Le système Domain CEGIS est maintenant prêt pour l'intégration avec l'Orchestrator v1 !** 🚀
