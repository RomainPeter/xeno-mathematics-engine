# Attribute Exploration (AE) — Next-Closure

## Vue d'ensemble

L'Attribute Exploration (AE) implémente l'algorithme Next-Closure de Ganter avec ordre lectique pour l'énumération complète des concepts FCA (Formal Concept Analysis).

## Algorithme Next-Closure

### Principe
- **Ordre lectique** : Les attributs sont triés alphabétiquement
- **Énumération complète** : Tous les concepts sont générés sans doublons
- **Relation de couverture** : Construction du diagramme de Hasse

### Implémentation
- `src/xme/engines/ae/next_closure.py` : Algorithme Next-Closure
- `src/xme/utils/fca.py` : Utilitaires FCA (intent_of, extent_of)
- `src/xme/engines/ae/psp_builder.py` : Construction PSP avec couverture Hasse

## Utilisation

### Commande CLI
```bash
xme ae demo --context tests/fixtures/fca/context_4x4.json --out artifacts/psp/ae_4x4.json
```

### Exemples de contextes
- `tests/fixtures/fca/context_4x4.json` : Contexte 4×4 (4 objets, 4 attributs)
- `tests/fixtures/fca/context_5x3.json` : Contexte 5×3 (5 objets, 3 attributs)

## Format des contextes FCA

```json
{
  "attributes": ["a", "b", "c", "d"],
  "objects": [
    {"id": "g1", "attrs": ["a", "b"]},
    {"id": "g2", "attrs": ["b", "c"]},
    {"id": "g3", "attrs": ["a", "c", "d"]},
    {"id": "g4", "attrs": ["b", "d"]}
  ]
}
```

## Garanties

### Déterminisme
- **Tri stable** : Les attributs sont triés alphabétiquement
- **Ordre lectique** : Respect de l'ordre de Ganter
- **Normalisation PSP** : Sortie canonique

### DAG (Directed Acyclic Graph)
- **Couverture Hasse** : Relations de couverture sans intermédiaires
- **Pas de cycles** : Vérification avec NetworkX
- **Structure hiérarchique** : Diagramme de concept complet

## Tests

### Golden Files
- `tests/golden/ae/context_4x4.intents.json` : Intents attendus pour 4×4
- `tests/golden/ae/context_5x3.intents.json` : Intents attendus pour 5×3

### Génération des Golden Files
```bash
python scripts/gen_goldens.py
```

### Tests de validation
- **Déterminisme** : Comparaison avec golden files
- **Pas de doublons** : Vérification unicité des concepts
- **DAG** : Validation de la structure sans cycles
- **CLI** : Test de l'intégration complète

## Performance

- **Temps d'exécution** : < 1s par cas de test
- **Déterminisme** : Sortie reproductible
- **Mémoire** : Optimisé pour petits contextes

## Intégration

L'algorithme Next-Closure est intégré dans l'orchestrator via :
- `src/xme/orchestrator/loops/ae.py` : Boucle AE asynchrone
- `src/xme/cli/main.py` : Commande CLI `xme ae demo`
- **PCAP logging** : Journalisation des actions
- **Timeout/Incidents** : Gestion des budgets temporels
