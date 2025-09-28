# Orchestrateur Industrialisé (AE/CEGIS)

## 🎯 Objectif

Industrialiser la pipeline Orchestrateur en remplaçant les boucles stub AE/CEGIS par des moteurs asynchrones injectables exécutant Next-Closure (FCA) et CEGIS réels, diffusant une télémétrie structurée via l'event bus, et persistant preuves/incidents (PCAP/Incident Journal) dans l'Audit Pack.

## 🏗️ Architecture

### Composants Principaux

- **AEEngine**: Moteur Next-Closure (FCA) réel avec algorithmes de fermeture
- **CegisEngine**: Boucle CEGIS asynchrone avec génération/raffinement
- **Orchestrator**: Coordinateur principal avec scheduling concurrent
- **EventBus**: Bus d'événements structuré avec corrélation
- **Persistence**: PCAP + Incident Journal + Audit Pack

### Interfaces

```python
# AE Engine
class AEEngine(ABC):
    async def next_closure_step(ctx: AEContext) -> AEResult
    async def initialize(domain_spec: Dict[str, Any]) -> None
    async def cleanup() -> None

# CEGIS Engine  
class CegisEngine(ABC):
    async def propose(ctx: CegisContext) -> Candidate
    async def verify(candidate: Candidate, ctx: CegisContext) -> Union[Verdict, Counterexample]
    async def refine(candidate: Candidate, counterexample: Counterexample, ctx: CegisContext) -> Candidate
```

## 🚀 Utilisation

### Démonstration Complète

```bash
# Démonstration end-to-end
make -f Makefile.orchestrator demo

# Démonstration rapide (timeouts courts)
make -f Makefile.orchestrator demo-quick

# Tests de validation
make -f Makefile.orchestrator test-demo
```

### Utilisation Programmatique

```python
from orchestrator.orchestrator import Orchestrator
from orchestrator.config import OrchestratorConfig
from orchestrator.engines.next_closure_engine import NextClosureEngine
from orchestrator.engines.cegis_async_engine import AsyncCegisEngine

# Configuration
config = OrchestratorConfig(
    ae_timeout=30.0,
    cegis_max_iterations=10,
    audit_dir="audit"
)

# Créer les moteurs
ae_engine = NextClosureEngine()
cegis_engine = AsyncCegisEngine(llm_adapter, verifier)

# Créer l'orchestrateur
orchestrator = Orchestrator(
    config=config,
    ae_engine=ae_engine,
    cegis_engine=cegis_engine,
    llm_adapter=llm_adapter,
    verifier=verifier,
    event_bus=event_bus
)

# Exécuter la pipeline
state = await orchestrator.run(domain_spec, budgets, thresholds)
```

## 📊 Fonctionnalités

### Next-Closure (FCA) Réel

- **Algorithme**: Next-Closure avec ordre lectique
- **Concepts**: Génération de concepts formels
- **Implications**: Extraction d'implications
- **Tests**: Contextes 4×4 et 5×3 avec invariants

### CEGIS Asynchrone

- **Génération**: Propose des candidats via LLM
- **Vérification**: Vérifie avec timeout/retries
- **Raffinement**: Refine basé sur contre-exemples
- **Concurrence**: LLM/Verifier en parallèle

### Event Bus Structuré

- **Corrélation**: trace_id, run_id, step_id
- **Types**: Orchestrator, AE, CEGIS, Verify, Incident
- **Logging**: JSON structuré avec niveaux
- **Métriques**: Temps, budgets, incidents

### Persistance

- **PCAP**: Proof-Carrying Action Plans
- **Incidents**: Journal des incidents avec sévérité
- **Audit Pack**: ZIP signé avec manifest/Merkle
- **Journal**: Entrées corrélées pour rejouabilité

## 🧪 Tests

### Tests Unitaires

```bash
# Tests Next-Closure
make -f Makefile.orchestrator test-next-closure

# Tests Orchestrateur
make -f Makefile.orchestrator test-orchestrator

# Tests complets
make -f Makefile.orchestrator test
```

### Tests d'Intégration

- **Mocks**: LLM/Verifier avec délais/timeouts
- **Concurrence**: Cancel restant sur incident
- **Eventing**: Séquence attendue, alignement logs/events
- **Audit Pack**: Fichiers présents, JSON valide, hash stable

## 📦 Audit Pack

### Structure

```
audit/
├── packs/
│   └── {run_id}/
│       ├── manifest.json      # Métadonnées + signatures
│       ├── pcaps.json         # Preuves PCAP
│       ├── incidents.json     # Journal incidents
│       ├── journal.jsonl      # Journal corrélé
│       ├── metrics.json       # Métriques
│       └── {run_id}.zip       # Archive signée
```

### Vérification

```python
# Vérifier l'intégrité
verification = await audit_pack_builder.verify_audit_pack(run_id)
if verification["valid"]:
    print(f"SHA256: {verification['sha256']}")
    print(f"Merkle: {verification['merkle_root']}")
```

## 🔧 Configuration

### OrchestratorConfig

```python
@dataclass
class OrchestratorConfig:
    # Timeouts
    ae_timeout: float = 30.0
    cegis_propose_timeout: float = 10.0
    cegis_verify_timeout: float = 15.0
    cegis_refine_timeout: float = 10.0
    
    # CEGIS parameters
    cegis_max_iterations: int = 10
    cegis_max_stable_no_improve: int = 3
    
    # Retry configuration
    max_retries: int = 3
    retry_backoff_base: float = 1.0
    
    # Determinism
    seed: Optional[int] = None
    hermetic_mode: bool = False
    
    # Audit configuration
    audit_dir: str = "audit"
    pcap_retention_days: int = 30
    incident_retention_days: int = 90
```

## 📈 Métriques

### Événements Publiés

- `orchestrator.started/completed/failed`
- `ae.started/step/completed/failed/timeout`
- `cegis.started/proposed/verified/refined/completed/failed/timeout`
- `verify.attempt/success/failed/timeout`
- `incident.raised/resolved`
- `budget.warning/overrun`
- `pcap.emitted/signed`
- `metrics.collected/summary`

### Métriques Collectées

- **Durée**: Temps total d'exécution
- **Concepts**: Nombre de concepts FCA générés
- **Implications**: Nombre d'implications extraites
- **Candidats**: Nombre de candidats CEGIS
- **Incidents**: Nombre et types d'incidents
- **Événements**: Nombre d'événements publiés

## 🎯 Critères d'Acceptation

### ✅ Fonctionnels

- [x] AE/CEGIS réels exécutés
- [x] Progression publiée via pefc.events
- [x] Logs JSON corrélés (run_id/step_id/trace_id)
- [x] Concurrence LLM/Verifier avec timeouts+retries
- [x] Timeout → Incident{FailReason=time_budget_exceeded}
- [x] Audit Pack contient PCAPs signables et incidents
- [x] Rejouabilité via journal.jsonl

### ✅ Tests

- [x] Tests verts: Next-Closure, CEGIS jouet, concurrence/cancel, eventing
- [x] Demo script produit artefacts attendus et verdict OK
- [x] Invariants FCA: pas de doublon, ordre total, fermeture idempotente
- [x] Concurrence: cancel restant sur incident, no-deadlock

### ✅ Démonstration

- [x] Demo end-to-end sur repo jouet
- [x] Orchestrateur exécute AE puis boucle CEGIS
- [x] Tâche de conformité code (règle d'API)
- [x] Événements temps-réel publiés
- [x] Audit Pack signé avec journal de preuves (PCAPs)
- [x] Incidents (FailReason), métriques, verdict

## 🚀 Démarrage Rapide

```bash
# 1. Installation
make -f Makefile.orchestrator install

# 2. Tests de validation
make -f Makefile.orchestrator test-demo

# 3. Démonstration
make -f Makefile.orchestrator demo

# 4. Analyse des résultats
make -f Makefile.orchestrator demo-audit
```

## 📚 Documentation

- **Architecture**: [orchestrator/](orchestrator/)
- **Engines**: [orchestrator/engines/](orchestrator/engines/)
- **Persistence**: [orchestrator/persistence/](orchestrator/persistence/)
- **Events**: [pefc/events/](pefc/events/)
- **Tests**: [tests/](tests/)

## 🎯 Prochaines Étapes

1. **Optimisation**: Performance des algorithmes FCA
2. **Intégration**: Connexion avec vrais LLM/Verifiers
3. **Monitoring**: Dashboard temps-réel
4. **Scaling**: Orchestration distribuée
5. **Security**: Signatures cryptographiques réelles
