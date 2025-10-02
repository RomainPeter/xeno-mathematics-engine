# Orchestrator Lite (AE)

## Vue d'ensemble

L'Orchestrator Lite implémente une boucle AE (Attribute Exploration) minimaliste sur un petit contexte FCA, produisant un PSP valide et journalisant en PCAP (S0) avec gestion des budgets/timeout et incidents.

## Architecture

### Composants principaux

- **État (RunState)** : `run_id`, budgets temporels, métriques
- **EventBus** : Queue asynchrone pour les événements
- **Boucle AE** : Timeout + incidents avec logging PCAP

### Boucle AE

1. **Chargement du contexte FCA** depuis un fichier JSON
2. **Énumération des concepts** via Next-Closure (algorithme réel)
3. **Construction du PSP** avec relation de couverture Hasse
4. **Logging PCAP S0** des actions et incidents
5. **Gestion des timeouts** avec incidents

### Boucle CEGIS

1. **Initialisation du domaine** avec secret bitvector
2. **Boucle propose→verify→refine** déterministe
3. **Convergence garantie** en ≤ L itérations pour secret de longueur L
4. **Logging PCAP S0** des actions (start, propose, verify_ok/fail, refine, done)
5. **Gestion des timeouts** avec incidents cegis_timeout

## Utilisation

### Commandes CLI

**AE (Attribute Exploration):**
```bash
xme ae demo --context examples/fca/context_4x4.json --out artifacts/psp/ae_demo.json
```

**CEGIS (Counter-Example Guided Inductive Synthesis):**
```bash
xme cegis demo --secret 10110 --max-iters 16 --out artifacts/cegis/result.json
```

### Options

**AE:**
- `--context` : Chemin vers le contexte FCA JSON
- `--out` : Chemin de sortie pour le PSP (défaut: `artifacts/psp/ae_demo.json`)
- `--run` : Chemin PCAP run (optionnel, crée un nouveau run si vide)
- `--ae-ms` : Budget timeout AE en millisecondes (défaut: 1500)

**CEGIS:**
- `--secret` : Vecteur de bits secret à synthétiser
- `--max-iters` : Nombre maximum d'itérations (défaut: 16)
- `--out` : Chemin de sortie pour le résultat (défaut: `artifacts/cegis/result.json`)
- `--run` : Chemin PCAP run (optionnel, crée un nouveau run si vide)
- `--cegis-ms` : Budget timeout CEGIS en millisecondes (défaut: 5000)

### Exemples de contextes

- `examples/fca/context_4x4.json` : Contexte 4×4 (4 objets, 4 attributs)
- `examples/fca/context_5x3.json` : Contexte 5×3 (5 objets, 3 attributs)

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

## Gestion des incidents

- **Timeout AE** : Loggé comme `incident.ae_timeout` avec budget_ms
- **Niveau S0** : Logging rapide pour les démonstrations
- **PCAP** : Journalisation tamper-evident des actions

## PSP généré

Le PSP contient :
- **Blocs** : Concepts avec id `c{k}`, label `{a,b}`, data.intent
- **Arêtes** : Relations de couverture Hasse (sans intermédiaires)
- **Méta** : `theorem: "AE Next-Closure"`

## Tests

**AE:**
- `test_ae_demo_produces_psp.py` : Vérifie la production d'un PSP valide
- `test_ae_timeout_incident.py` : Vérifie la gestion des timeouts

**CEGIS:**
- `test_cegis_converges.py` : Vérifie la convergence en ≤ L itérations
- `test_cegis_pcap_logs.py` : Vérifie les logs PCAP (propose, verify, refine)
- `test_cegis_timeout_incident.py` : Vérifie la gestion des timeouts
