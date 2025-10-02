# E-graph v0 — Canonicalisation et Signatures Structurelles

L'e-graph v0 de XME implémente un système minimaliste de canonicalisation d'expressions avec alpha-renaming, hash-consing, et signatures structurelles. Il évite la redondance structurelle en normalisant les expressions selon des règles commutatives et d'alpha-équivalence.

## Vue d'ensemble

L'e-graph v0 fournit :

- **Alpha-renaming** : Normalisation des variables libres (var:x → var:_1, var:_2 par ordre d'apparition)
- **Hash-consing** : Interning des nœuds pour éviter la duplication
- **Signatures canoniques** : SHA256 des expressions normalisées
- **Règles commutatives** : Normalisation des opérateurs commutatifs
- **CLI** : Commandes pour canonicaliser et tester l'égalité structurelle

## Architecture

### Nœuds

Les nœuds de l'e-graph sont définis dans `src/xme/egraph/node.py` :

```python
@dataclass
class Node:
    op: str                    # Opérateur
    args: List[NodeId]        # Arguments (IDs de nœuds)
    attrs: Dict[str, Any]     # Attributs triés
```

**Types de nœuds :**

- **Atom** : Symboles et constantes (`{"op": "atom", "attrs": {"symbol": "x"}}`)
- **Value** : Nombres et strings (`{"op": "value", "attrs": {"value": 42}}`)
- **Variable** : Variables avec alpha-renaming (`{"op": "var", "attrs": {"name": "x"}}`)

### Alpha-renaming

L'alpha-renaming normalise les variables libres selon l'ordre d'apparition :

```python
# Variables originales
expr = {
    "op": "+",
    "args": [
        {"op": "var", "name": "x"},
        {"op": "var", "name": "y"}
    ]
}

# Après alpha-renaming
renamed = {
    "op": "+",
    "args": [
        {"op": "var", "name": "_1"},
        {"op": "var", "name": "_2"}
    ]
}
```

**Propriétés :**

- **Invariant** : Deux expressions alpha-équivalentes → même signature
- **Ordre d'apparition** : Variables renommées par ordre de première occurrence
- **Récursif** : Fonctionne sur des expressions imbriquées

### Hash-consing

Le hash-consing évite la duplication de nœuds identiques :

```python
class HashCons:
    def intern(self, node: Dict[str, Any]) -> NodeId:
        """Interne un nœud et retourne son ID stable."""
        key = self._canonical_key(node)
        if key in self._intern:
            return self._intern[key]  # Nœud existant
        # Créer nouveau nœud
```

**Avantages :**

- **Déduplication** : Nœuds identiques partagent le même ID
- **Efficacité** : Évite la duplication mémoire
- **Stabilité** : IDs stables pour les nœuds canoniques

### E-graph

L'e-graph gère les classes d'équivalence :

```python
class EGraph:
    def add_node(self, node: Dict[str, Any]) -> NodeId:
        """Ajoute un nœud à l'e-graph."""
    
    def merge(self, node_id1: NodeId, node_id2: NodeId):
        """Fusionne deux nœuds dans la même classe d'équivalence."""
    
    def are_equal(self, node_id1: NodeId, node_id2: NodeId) -> bool:
        """Vérifie si deux nœuds sont égaux."""
```

## Canonicalisation

### Règles de canonicalisation

La canonicalisation suit ces étapes :

1. **Alpha-renaming** : Variables renommées par ordre d'apparition
2. **Normalisation commutative** : Arguments triés pour opérateurs commutatifs
3. **Tri des attributs** : Attributs triés lexicographiquement
4. **Signature** : SHA256 du parcours postfix canonique

### Opérateurs commutatifs

Les opérateurs suivants sont traités comme commutatifs :

```python
COMMUTATIVE_OPS = {"+", "*", "and", "or", "∧", "∨", "&", "|"}
```

**Exemple :**

```json
// Expression originale
{
  "op": "+",
  "args": [
    {"op": "var", "name": "y"},
    {"op": "var", "name": "x"}
  ]
}

// Après canonicalisation
{
  "op": "+",
  "args": [
    {"op": "var", "name": "_1"},
    {"op": "var", "name": "_2"}
  ]
}
```

### Signature structurelle

La signature est calculée via un parcours postfix des tokens canoniques :

```python
def generate_signature(expr: Dict[str, Any]) -> str:
    tokens = postfix_traversal(expr)
    serialized = json.dumps(tokens, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()
```

**Propriétés :**

- **Déterministe** : Même expression → même signature
- **Structurelle** : Expressions structurellement égales → même signature
- **Alpha-invariante** : Expressions alpha-équivalentes → même signature

## Format d'entrée

### Structure JSON

Les expressions sont représentées en JSON avec cette structure :

```json
{
  "op": "opérateur",
  "args": [/* arguments */],
  "attrs": {/* attributs optionnels */}
}
```

### Exemples

**Addition commutative :**

```json
{
  "op": "+",
  "args": [
    {"op": "var", "name": "x"},
    {"op": "var", "name": "y"}
  ]
}
```

**Expression imbriquée :**

```json
{
  "op": "compose",
  "args": [
    {
      "op": "+",
      "args": [
        {"op": "var", "name": "f"},
        {"op": "var", "name": "g"}
      ]
    },
    {
      "op": "*",
      "args": [
        {"op": "value", "attrs": {"value": 2}},
        {"op": "var", "name": "x"}
      ]
    }
  ]
}
```

## CLI

### Commandes disponibles

**Canonicalisation :**

```bash
xme egraph canon --in input.json --out output.json
```

**Comparaison d'égalité :**

```bash
xme egraph equal --a expr1.json --b expr2.json
```

### Exemples d'utilisation

**Canonicaliser une expression :**

```bash
# Input: examples/egraph/add_comm.json
xme egraph canon --in examples/egraph/add_comm.json --out artifacts/egraph/add_comm.canon.json
```

**Tester l'égalité structurelle :**

```bash
# Test que add_comm.json == add_comm_swapped.json
xme egraph equal --a examples/egraph/add_comm.json --b examples/egraph/add_comm_swapped.json
# Exit code: 0 (égales)
```

## Contraintes et limites v0

### Contraintes actuelles

1. **Opérateurs commutatifs limités** : Seuls `+`, `*`, `and`, `or`, `∧`, `∨`, `&`, `|` sont traités comme commutatifs
2. **Pas de règles de réécriture** : Aucune règle de transformation automatique
3. **Pas de congruence** : Les classes d'équivalence ne sont pas propagées automatiquement
4. **Pas de saturation** : L'e-graph ne sature pas les règles

### Limites v0

1. **Performance** : Pas d'optimisations avancées pour de gros e-graphs
2. **Règles complexes** : Pas de support pour des règles de réécriture complexes
3. **Persistence** : Pas de sauvegarde/chargement d'e-graphs
4. **Visualisation** : Pas d'outils de visualisation

### Extensions futures

1. **Règles de réécriture** : Support pour des règles de transformation
2. **Congruence** : Propagation automatique des classes d'équivalence
3. **Saturation** : Algorithme de saturation des règles
4. **Performance** : Optimisations pour de gros e-graphs
5. **Persistence** : Sauvegarde/chargement d'e-graphs
6. **Visualisation** : Outils de visualisation graphique

## Tests

### Tests d'alpha-renaming

```python
def test_alpha_equivalent_same_vars():
    """var:x, var:y vs var:a, var:b → même sig"""
    expr1 = {"op": "+", "args": [{"op": "var", "name": "x"}, {"op": "var", "name": "y"}]}
    expr2 = {"op": "+", "args": [{"op": "var", "name": "a"}, {"op": "var", "name": "b"}]}
    assert is_alpha_equivalent(expr1, expr2)
```

### Tests commutatifs

```python
def test_commutative_addition():
    """add_comm.json vs swapped → même sig"""
    expr1 = {"op": "+", "args": [{"op": "var", "name": "x"}, {"op": "var", "name": "y"}]}
    expr2 = {"op": "+", "args": [{"op": "var", "name": "y"}, {"op": "var", "name": "x"}]}
    assert are_structurally_equal(expr1, expr2)
```

### Tests non-commutatifs

```python
def test_compose_order_matters():
    """("compose", f,g) vs (g,f) → sig différent"""
    expr1 = {"op": "compose", "args": [{"op": "var", "name": "f"}, {"op": "var", "name": "g"}]}
    expr2 = {"op": "compose", "args": [{"op": "var", "name": "g"}, {"op": "var", "name": "f"}]}
    assert not are_structurally_equal(expr1, expr2)
```

## Intégration

### Makefile

```makefile
egraph-canon:
	@xme egraph canon --in examples/egraph/add_comm.json --out artifacts/egraph/add_comm.canon.json
```

### CI

Les tests e-graph sont intégrés dans la CI :

```yaml
pytest:
  steps:
    - run: nix develop -c pytest tests/test_egraph_*.py
```

## Références

- [E-graphs: A Core Data Structure](https://egraphs-good.github.io/)
- [Alpha-equivalence](https://en.wikipedia.org/wiki/Alpha_equivalence)
- [Hash-consing](https://en.wikipedia.org/wiki/Hash_consing)
- [Commutative operations](https://en.wikipedia.org/wiki/Commutative_property)
