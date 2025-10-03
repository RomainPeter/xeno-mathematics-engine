# Referee H/X - Gouvernance bifocale opérationnelle

Le Referee H/X implémente une gouvernance bifocale pour la gestion des espaces H (Human) et X (Xeno), avec des budgets, des embargos et des baptêmes contrôlés.

## 🎯 Vue d'ensemble

Le Referee H/X fournit trois mécanismes de gouvernance :

1. **Budgets H/X** : Contrôle des quotas pour les espaces H et X
2. **Alien Reserves** : Embargo des X-lineages
3. **PCN Symbol Forge** : Baptême contrôlé des symboles avec preuves

## 📊 Budgets H/X

### Configuration

```yaml
budgets:
  h_quota: 10    # Quota pour l'espace H
  x_quota: 20    # Quota pour l'espace X
```

### Utilisation

```python
from xme.referee.budgets import BudgetsHX, BudgetTracker

# Créer un tracker
tracker = BudgetTracker(BudgetsHX(h_quota=10, x_quota=20))

# Consommer du budget
if tracker.consume("H", 5):
    print("Budget H consommé avec succès")
else:
    print("Budget H insuffisant")

# Vérifier le budget restant
remaining = tracker.remaining("X")
print(f"Budget X restant: {remaining}")

# Obtenir un rapport
report = tracker.report()
print(f"H utilisé: {report['H_used']}, restant: {report['H_remaining']}")
```

## 🚫 Alien Reserves (Embargos)

### Gestion des embargos

```python
from xme.referee.alien_reserve import AlienReserve

# Créer un reserve
reserve = AlienReserve(Path("artifacts/referee/reserve.json"))

# Enregistrer un lineage sous embargo
reserve.register("X123", {"area": "demo", "risk": "high"})

# Vérifier l'embargo
if reserve.is_embargoed("X123"):
    print("Lineage X123 sous embargo")

# Libérer un lineage
reserve.release("X123", "criteria met")
```

### CLI pour les embargos

```bash
# Ajouter un lineage à l'embargo
xme referee embargo-add --lineage X123 --meta '{"area":"demo","risk":"high"}'

# Libérer un lineage
xme referee embargo-release --lineage X123 --reason "criteria met"

# Voir le statut
xme referee status
```

## 🔐 PCN Symbol Forge

### Baptême de symboles

Le baptême de symboles nécessite :
- Un lineage non-embargoé
- Un symbole respectant le charset (A-Za-z0-9_)
- Une référence de preuve (proof_ref)

```python
from xme.referee.referee import Referee

# Créer le Referee
referee = Referee(
    cfg_path=Path("config/referee.yaml"),
    reserve_path=Path("artifacts/referee/reserve.json"),
    symbols_path=Path("artifacts/referee/symbols.json")
)

# Baptiser un symbole
verdict = referee.gate_baptism(
    lineage_id="X123",
    concept_id="C42",
    symbol="Xi_1",
    proof_ref="psp:proof123"
)

if verdict["ok"]:
    print(f"Symbole baptisé: {verdict['entry']}")
else:
    print(f"Baptême refusé: {verdict['reason']}")
```

### CLI pour le baptême

```bash
# Baptiser un symbole
xme symbol baptize \
  --concept C42 \
  --symbol Xi_1 \
  --proof-ref "psp:proof123" \
  --lineage X123

# Avec logging PCAP
xme symbol baptize \
  --concept C42 \
  --symbol Xi_1 \
  --proof-ref "psp:proof123" \
  --lineage X123 \
  --run artifacts/pcap/run-123.jsonl
```

## 🔧 Configuration

### Fichier de configuration

```yaml
budgets:
  h_quota: 10
  x_quota: 20

embargo_rules:
  min_checks: ["psp:S1"]

naming:
  allowed_charset: "^[A-Za-z0-9_]+$"
```

### Paramètres

- **h_quota** : Quota pour l'espace H (défaut: 10)
- **x_quota** : Quota pour l'espace X (défaut: 20)
- **min_checks** : Vérifications minimales requises pour la libération
- **allowed_charset** : Expression régulière pour les noms de symboles

## 📝 Journalisation PCAP

Toutes les actions du Referee sont loguées dans PCAP :

```json
{
  "action": "referee.budget_consume",
  "obligations": {
    "budget.H": "true"
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

```json
{
  "action": "symbol.baptize.accept",
  "obligations": {
    "pcn.proof_ref:exists": "true"
  },
  "psp_ref": "psp:proof123",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

## 🧪 Tests

```bash
# Tests des budgets
python -m pytest tests/test_referee_budgets.py -v

# Tests des embargos
python -m pytest tests/test_alien_reserve_embargo.py -v

# Tests du PCN
python -m pytest tests/test_pcn_requires_proofref.py -v
```

## 🎯 Cas d'usage

### Workflow complet

1. **Initialisation** : Créer les fichiers de configuration et de données
2. **Embargo** : Mettre sous embargo les X-lineages suspects
3. **Vérification** : Effectuer les vérifications requises (PSP S1, etc.)
4. **Libération** : Libérer les lineages qui passent les vérifications
5. **Baptême** : Baptiser les symboles avec preuves valides

### Exemple d'intégration

```python
# Dans un pipeline de découverte
from xme.referee.referee import Referee

def run_discovery_with_governance():
    referee = Referee(cfg_path, reserve_path, symbols_path)

    # Vérifier les budgets
    if not referee.enforce_budgets("X", 5, pcap_store):
        raise Exception("Budget X insuffisant")

    # Exécuter la découverte
    result = run_discovery()

    # Baptiser les nouveaux symboles
    for concept in result.concepts:
        verdict = referee.gate_baptism(
            lineage_id=result.lineage_id,
            concept_id=concept.id,
            symbol=concept.symbol,
            proof_ref=concept.proof_ref,
            pcap=pcap_store
        )

        if not verdict["ok"]:
            print(f"Baptême refusé: {verdict['reason']}")
```

## 🔍 Dépannage

### Problèmes courants

1. **Budget insuffisant** : Vérifier les quotas dans la configuration
2. **Lineage sous embargo** : Libérer le lineage avec `embargo-release`
3. **Symbole invalide** : Vérifier le charset (A-Za-z0-9_)
4. **Preuve manquante** : Fournir une référence de preuve valide

### Logs et débogage

```bash
# Voir le statut complet
xme referee status

# Vérifier les embargos
xme referee embargo-add --lineage X123 --meta '{"debug":true}'
xme referee embargo-release --lineage X123 --reason "debug ok"
```
