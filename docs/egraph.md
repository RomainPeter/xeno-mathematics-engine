# E-graph v1 : Réécritures + Saturation + Extraction par coût

## Vue d'ensemble

L'E-graph v1 implémente un système de réécriture déclarative avec saturation jusqu'au fixpoint et extraction par coût. Il utilise la signature canonique (PR #13) pour dédupliquer les formes et éviter la redondance structurelle.

## Architecture

### Composants principaux

1. **DSL de patterns** (`src/xme/egraph/rules.py`)
   - Patterns avec variables, constantes et opérations
   - Matching et substitution
   - Règles de réécriture LHS → RHS

2. **Moteur de saturation** (`src/xme/egraph/engine.py`)
   - Exploration des formes atteignables
   - Déduplication par signature canonique
   - Limites de sécurité (max_iters, seen_limit)

3. **Système de coûts** (`src/xme/egraph/cost.py`)
   - Coût basé sur le nombre de nœuds
   - Coût pondéré par opérateur
   - Extraction de la forme optimale

## DSL de patterns

### Types d'expressions

```python
# Variable
{"var": "x"}

# Constante
{"const": 42}

# Opération
{"op": "+", "args": [{"var": "x"}, {"var": "y"}]}
```

### Règles de réécriture

```python
from xme.egraph.rules import Rule

# Simplification : x * 1 → x
rule = Rule(
    lhs={"op": "*", "args": [{"var": "x"}, {"const": 1}]},
    rhs={"var": "x"},
    name="mul_unit_right"
)
```

### Matching et substitution

```python
from xme.egraph.rules import match, substitute

# Matching
env = match(expr, pattern)
if env is not None:
    # Pattern matché, env contient les variables

# Substitution
new_expr = substitute(pattern, env)
```

## Moteur de saturation

### Saturation jusqu'au fixpoint

```python
from xme.egraph.engine import saturate

# Saturer une expression
forms = saturate(expr, rules, max_iters=50, seen_limit=5000)
```

**Paramètres :**
- `max_iters` : Nombre maximum d'itérations (défaut: 50)
- `seen_limit` : Limite du nombre de formes vues (défaut: 5000)

**Algorithme :**
1. Explore les formes atteignables via réécritures
2. Déduplique par signature canonique
3. S'arrête au fixpoint ou aux limites

### Extraction par coût

```python
from xme.egraph.engine import extract_best
from xme.egraph.cost import cost_nodes

# Extraire la meilleure forme
best = extract_best(forms, cost_fn=cost_nodes)
```

## Système de coûts

### Coût basé sur les nœuds

```python
from xme.egraph.cost import cost_nodes

cost = cost_nodes(expr)  # Nombre de nœuds dans l'expression
```

### Coût pondéré

```python
from xme.egraph.cost import cost_weighted

# Définir les poids
weights = {"*": 1, "+": 2, "leaf": 1}
cost_fn = cost_weighted(weights)

cost = cost_fn(expr)  # Coût pondéré
```

## Commandes CLI

### Saturation

```bash
# Saturer une expression
xme egraph saturate --in examples/egraph/unit_mul.json \
                    --rules examples/egraph/rules/arith.json \
                    --out artifacts/egraph/simplified.json

# Avec extraction pondérée
xme egraph saturate --in expr.json \
                    --extract "weights:{\"*\":1,\"+\":2}" \
                    --out result.json
```

### Explication d'équivalence

```bash
# Vérifier si deux expressions sont équivalentes
xme egraph explain --a examples/egraph/add_comm.json \
                   --b examples/egraph/add_comm_swapped.json
```

## Exemples d'usage

### Simplification des unités

```python
# Expression : x * 1 + 0
expr = {"op": "+", "args": [{"op": "*", "args": [{"var": "x"}, {"const": 1}]}, {"const": 0}]}

# Règles de simplification
rules = [
    Rule(lhs={"op": "*", "args": [{"var": "x"}, {"const": 1}]}, rhs={"var": "x"}),
    Rule(lhs={"op": "+", "args": [{"var": "x"}, {"const": 0}]}, rhs={"var": "x"}),
]

# Résultat : x
forms = saturate(expr, rules)
best = extract_best(forms, cost_fn=cost_nodes)
# best == {"var": "x"}
```

### Commutativité et associativité

```python
# Les expressions (a+b)+c et c+(b+a) mènent à la même forme canonique
e1 = {"op": "+", "args": [{"op": "+", "args": [{"var": "a"}, {"var": "b"}]}, {"var": "c"}]}
e2 = {"op": "+", "args": [{"var": "c"}, {"op": "+", "args": [{"var": "b"}, {"var": "a"}]}]}

# Après saturation, elles ont la même signature canonique
_, s1 = canonicalize(extract_best(saturate(e1, rules), cost_fn))
_, s2 = canonicalize(extract_best(saturate(e2, rules), cost_fn))
assert s1 == s2
```

### Distribution optionnelle

```python
# Expression : x * (y + z)
expr = {"op": "*", "args": [{"var": "x"}, {"op": "+", "args": [{"var": "y"}, {"var": "z"}]}]}

# Règle de distribution
rule = Rule(
    lhs={"op": "*", "args": [{"var": "x"}, {"op": "+", "args": [{"var": "y"}, {"var": "z"}]}]},
    rhs={"op": "+", "args": [{"op": "*", "args": [{"var": "x"}, {"var": "y"}]},
                              {"op": "*", "args": [{"var": "x"}, {"var": "z"}]}]}
)

# Avec coût pondéré, la distribution peut être optionnelle
forms = saturate(expr, [rule])
best = extract_best(forms, cost_fn=cost_weighted({"*": 1, "+": 2}))
```

## Règles d'exemple

### Règles arithmétiques

```json
[
  {
    "name": "mul_unit_right",
    "lhs": {"op": "*", "args": [{"var": "x"}, {"const": 1}]},
    "rhs": {"var": "x"}
  },
  {
    "name": "add_zero_right",
    "lhs": {"op": "+", "args": [{"var": "x"}, {"const": 0}]},
    "rhs": {"var": "x"}
  },
  {
    "name": "add_comm",
    "lhs": {"op": "+", "args": [{"var": "x"}, {"var": "y"}]},
    "rhs": {"op": "+", "args": [{"var": "y"}, {"var": "x"}]}
  }
]
```

## Limites et sécurité

### Limites de saturation

- **max_iters** : Évite les boucles infinies
- **seen_limit** : Contrôle la mémoire utilisée
- **Déduplication** : Évite la redondance via signatures canoniques

### Bonnes pratiques

1. **Règles confluentes** : Éviter les conflits entre règles
2. **Limites raisonnables** : Ajuster max_iters selon la complexité
3. **Coûts appropriés** : Choisir des fonctions de coût cohérentes

## Tests

### Tests unitaires

```bash
# Tests de simplification
python -m pytest tests/test_rewrites_simplify_units.py -v

# Tests de commutativité/associativité
python -m pytest tests/test_rewrites_comm_assoc_canon.py -v

# Tests de distribution
python -m pytest tests/test_rewrites_distribution_opt_in.py -v
```

### Tests d'intégration

```bash
# Test complet avec CLI
xme egraph saturate --in examples/egraph/unit_mul.json \
                    --rules examples/egraph/rules/arith.json \
                    --out artifacts/egraph/simplified.json

# Vérifier le résultat
cat artifacts/egraph/simplified.json
# Devrait contenir {"var": "x"}
```

## Intégration avec PR #13

L'E-graph v1 utilise la signature canonique de PR #13 pour :

1. **Déduplication** : Éviter les formes redondantes
2. **Équivalence** : Détecter les expressions équivalentes
3. **Optimisation** : Réduire l'espace de recherche

```python
from xme.egraph.canon import canonicalize

# Canonicaliser avant comparaison
canon_expr, signature = canonicalize(expr)
```

## Cas d'usage avancés

### Optimisation de code

```python
# Expression complexe
expr = {"op": "+", "args": [
    {"op": "*", "args": [{"var": "x"}, {"const": 1}]},
    {"op": "*", "args": [{"const": 0}, {"var": "y"}]}
]}

# Simplification automatique
forms = saturate(expr, simplification_rules)
best = extract_best(forms, cost_fn=cost_nodes)
# Résultat : {"var": "x"}
```

### Vérification d'équivalence

```python
# Vérifier que deux expressions sont équivalentes
def are_equivalent(expr1, expr2, rules):
    forms1 = saturate(expr1, rules)
    forms2 = saturate(expr2, rules)

    best1 = extract_best(forms1, cost_fn=cost_nodes)
    best2 = extract_best(forms2, cost_fn=cost_nodes)

    _, sig1 = canonicalize(best1)
    _, sig2 = canonicalize(best2)

    return sig1 == sig2
```

## Dépannage

### Problèmes courants

1. **Saturation infinie** : Augmenter max_iters ou seen_limit
2. **Mémoire insuffisante** : Réduire seen_limit
3. **Règles conflictuelles** : Vérifier la confluence des règles

### Debug

```python
# Vérifier les formes générées
forms = saturate(expr, rules, max_iters=10)
print(f"Generated {len(forms)} forms")

# Vérifier les coûts
for i, form in enumerate(forms):
    cost = cost_nodes(form)
    print(f"Form {i}: cost={cost}")
```

## Roadmap

### Améliorations futures

1. **Règles conditionnelles** : Patterns avec conditions
2. **Saturation incrémentale** : Mise à jour des formes existantes
3. **Parallélisation** : Saturation distribuée
4. **Règles dynamiques** : Ajout/suppression de règles à l'exécution

### Intégration

- **PSP** : Génération de preuves de réécriture
- **PCAP** : Journalisation des transformations
- **Verifier** : Vérification des équivalences
