# Métriques & δ (Adjunction Defect)

Le système de métriques XME mesure la friction entre génération et vérification à travers l'**adjunction defect δ**, une métrique normalisée entre 0 et 1 où 0 = parfait et 1 = échec total.

## Définitions v1

### AE (Attribute Exploration)
**δ_ae = 1 - (|E_cover_validées| / |E_cover_proposées|)** si S1 échoue partiellement ; sinon 0

- **0.0** : Toutes les arêtes de couverture validées (parfait)
- **0.5** : La moitié des arêtes validées (friction modérée)
- **1.0** : Aucune arête validée (échec total)

### CEGIS (Counter-Example Guided Inductive Synthesis)
**δ_cegis = (iters_fail / iters_total)** ou 1 si non convergence sous budget

- **0.0** : Convergence immédiate (parfait)
- **0.5** : Convergence à mi-parcours (friction modérée)
- **1.0** : Non convergence ou échec total

### Run (Agrégation)
**δ_run = moyenne pondérée** (poids par durée ou count actions)

- Agrégation des δ par phase avec pondération
- Intégration des métriques temporelles et de performance

## Utilisation

### Commandes CLI

```bash
# Synthèse complète d'un run
xme metrics summarize --run artifacts/pcap/run-123.jsonl

# Synthèse en JSON
xme metrics summarize --run artifacts/pcap/run-123.jsonl --json

# Calcul des δ spécifiques
xme metrics delta --run artifacts/pcap/run-123.jsonl

# δ d'une phase spécifique
xme metrics delta --run artifacts/pcap/run-123.jsonl --phase ae

# Comparaison de deux runs
xme metrics compare --run1 artifacts/pcap/run-1.jsonl --run2 artifacts/pcap/run-2.jsonl
```

### API Python

```python
from xme.metrics.delta import compute_delta_ae, compute_delta_cegis, aggregate_run_delta
from xme.metrics.summarize import summarize_run

# Calculer δ_ae
delta_ae = compute_delta_ae(psp_before, psp_after)

# Calculer δ_cegis
delta_cegis = compute_delta_cegis(cegis_trace)

# Agrégation run
delta_info = aggregate_run_delta(Path("artifacts/pcap/run-123.jsonl"))

# Synthèse complète
summary = summarize_run(Path("artifacts/pcap/run-123.jsonl"))
```

## Structure des Résumés

### Résumé JSON

```json
{
  "run_path": "artifacts/pcap/run-123.jsonl",
  "total_entries": 25,
  "start_time": "2024-01-01T12:00:00Z",
  "end_time": "2024-01-01T12:05:00Z",
  "actions": {
    "ae_psp_emitted": 3,
    "cegis_start": 2,
    "discovery_turn_done": 5
  },
  "incidents": [
    {
      "timestamp": "2024-01-01T12:02:00Z",
      "action": "ae_timeout",
      "level": "S0",
      "type": "timeout",
      "details": {
        "obligations": {},
        "deltas": {}
      }
    }
  ],
  "deltas": {
    "delta_run": 0.25,
    "deltas_by_phase": {
      "ae": 0.3,
      "cegis": 0.2
    },
    "phase_weights": {
      "ae": 3,
      "cegis": 2
    }
  },
  "level_stats": {
    "S0": {"count": 20, "actions": ["ae_psp_emitted", "cegis_start"]},
    "S1": {"count": 5, "actions": ["verification_verdict"]}
  },
  "performance": {
    "total_actions": 25,
    "unique_actions": 8,
    "incident_rate": 0.04,
    "delta_run": 0.25,
    "phases_with_deltas": 2
  },
  "merkle_root": "abc123def456",
  "summary": "Run with 25 entries, 1 incidents, δ=0.250"
}
```

## Exemples

### Cas d'usage typiques

#### 1. Run AE parfait
```json
{
  "deltas": {"delta_run": 0.0},
  "incidents": [],
  "summary": "Run with 10 entries, 0 incidents, δ=0.000"
}
```

#### 2. Run avec friction modérée
```json
{
  "deltas": {"delta_run": 0.3},
  "incidents": [{"type": "timeout"}],
  "summary": "Run with 15 entries, 1 incidents, δ=0.300"
}
```

#### 3. Run avec échec total
```json
{
  "deltas": {"delta_run": 1.0},
  "incidents": [{"type": "error"}, {"type": "verification_failure"}],
  "summary": "Run with 5 entries, 2 incidents, δ=1.000"
}
```

### Comparaison de runs

```bash
# Comparer deux runs
xme metrics compare --run1 run-good.jsonl --run2 run-bad.jsonl
```

**Sortie :**
```
Run Comparison
Run 1: run-good.jsonl
Run 2: run-bad.jsonl
Summary: δ: 0.100 → 0.800 (degraded)

Delta comparison:
  Run 1 δ: 0.100
  Run 2 δ: 0.800
  Difference: +0.700
  Improvement: No

Entries comparison:
  Run 1: 20
  Run 2: 15
  Difference: -5

Incidents comparison:
  Run 1: 0
  Run 2: 3
  Difference: +3
```

## Limites et Contraintes

### Bornes des δ
- **δ ∈ [0, 1]** : Toutes les métriques sont automatiquement bornées
- **Validation** : Les valeurs invalides sont rejetées avec erreur
- **Précision** : Calculs en float64 avec arrondi à 3 décimales

### Limitations v1
- **Temporalité** : Pas de métriques temporelles avancées (v2)
- **Corrélation** : Pas d'analyse de corrélation entre phases (v2)
- **Prédiction** : Pas de modèles prédictifs (v3)

### Gestion d'erreurs
- **Fichiers manquants** : δ = 1.0 (échec total)
- **Données corrompues** : δ = 1.0 (échec total)
- **Runs vides** : δ = 0.0 (neutre)

## Intégration

### Avec les PR précédentes
- **PR #7** : Orchestrator Lite → métriques AE/CEGIS
- **PR #8** : AE Next-Closure → δ_ae basé sur couverture Hasse
- **PR #10** : CEGIS v0 → δ_cegis basé sur convergence
- **PR #11** : Discovery → δ_run agrégé
- **PR #14** : Verifier v1 → incidents et obligations

### Workflow typique
1. **Génération** : AE/CEGIS produit des artefacts
2. **Vérification** : Verifier v1 valide avec obligations
3. **Métriques** : Calcul des δ et synthèse
4. **Analyse** : Comparaison et optimisation

## Makefile

```makefile
# Cible pour analyser le dernier run
run-metrics:
	@xme metrics summarize --run "$(ls -1 artifacts/pcap/run-*.jsonl | tail -1)" --json
```

## Tests

```bash
# Tests des bornes δ
python -m pytest tests/test_metrics_delta_bounds.py -v

# Tests de synthèse
python -m pytest tests/test_metrics_summarize_includes_merkle.py -v
```

## Évolutions futures

### v2 (Métriques temporelles)
- **Latence** : Temps de génération vs vérification
- **Throughput** : Artefacts par unité de temps
- **Corrélation** : Relations entre phases

### v3 (Métriques prédictives)
- **Modèles** : Prédiction des δ basée sur l'historique
- **Optimisation** : Suggestions d'amélioration
- **Alertes** : Seuils de performance
