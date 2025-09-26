# Demo Repository - Proof Engine for Code v0

Ce repository de démonstration contient des exemples de code avec des violations intentionnelles pour tester le Proof Engine.

## Structure

```
demo_repo/
├── src/                    # Code source
│   ├── sanitize.py        # Module de sanitisation
│   ├── rate_limiter.py    # Module de limitation de débit
│   └── pure_fn.py         # Module de fonctions pures
└── tests/                 # Tests
    ├── test_sanitize.py   # Tests de sanitisation
    ├── test_rate_limiter.py # Tests de limitation
    └── test_pure_fn.py    # Tests de fonctions pures
```

## Modules

### 1. Sanitisation (`src/sanitize.py`)

Module de sanitisation des entrées utilisateur avec des fonctions pour:
- Échapper les caractères spéciaux
- Valider les emails
- Nettoyer le HTML
- Échapper les chaînes SQL

**Violations intentionnelles:**
- Manque de docstrings sur certaines fonctions
- Complexité cyclomatique élevée
- Pas de gestion d'erreurs robuste

### 2. Limitation de débit (`src/rate_limiter.py`)

Module de limitation de débit avec:
- RateLimiter basé sur un bucket de tokens
- SlidingWindowRateLimiter avec fenêtre glissante
- RateLimitManager pour plusieurs clients

**Violations intentionnelles:**
- Imports non utilisés
- Variables non typées
- Pas de gestion des exceptions

### 3. Fonctions pures (`src/pure_fn.py`)

Module de fonctions pures avec:
- Calcul de Fibonacci
- Factorisation en nombres premiers
- Statistiques mathématiques
- Algorithmes de tri et recherche

**Violations intentionnelles:**
- Fonctions trop longues
- Complexité élevée
- Pas de validation des entrées

## Tests

Chaque module a ses tests correspondants dans le répertoire `tests/`.

### Exécution des tests

```bash
# Tous les tests
pytest tests/

# Tests spécifiques
pytest tests/test_sanitize.py
pytest tests/test_rate_limiter.py
pytest tests/test_pure_fn.py
```

## Violations intentionnelles

Ce repository contient des violations intentionnelles pour tester le Proof Engine:

1. **Tests**: Certains tests peuvent échouer
2. **Linting**: Code non conforme aux standards
3. **Types**: Annotations de type manquantes
4. **Sécurité**: Vulnérabilités potentielles
5. **Complexité**: Code trop complexe
6. **Documentation**: Docstrings manquantes

## Utilisation avec le Proof Engine

Le Proof Engine peut être utilisé pour:

1. **Analyser** les violations
2. **Générer** des patches de correction
3. **Appliquer** les corrections
4. **Vérifier** la conformité
5. **Mesurer** l'amélioration

## Exemples de violations

### Sanitisation
```python
# Violation: pas de validation des entrées
def sanitize_input(user_input):
    return re.escape(user_input)  # Pas de vérification de None
```

### Limitation de débit
```python
# Violation: pas de gestion d'erreurs
def consume(self, tokens=1):
    if self.tokens >= tokens:
        self.tokens -= tokens
        return True
    return False  # Pas de logging ou d'erreur
```

### Fonctions pures
```python
# Violation: fonction trop complexe
def calculate_statistics(numbers):
    # 50+ lignes de code dans une seule fonction
    # Pas de validation des entrées
    # Complexité cyclomatique élevée
```

## Améliorations possibles

Le Proof Engine peut proposer des améliorations comme:

1. **Ajout de docstrings**
2. **Réduction de la complexité**
3. **Amélioration de la sécurité**
4. **Optimisation des performances**
5. **Meilleure gestion d'erreurs**
6. **Tests supplémentaires**

## Métriques de qualité

Le Proof Engine mesure:

- **Taux de succès des tests**
- **Conformité au linting**
- **Qualité des types**
- **Score de sécurité**
- **Complexité cyclomatique**
- **Couverture de documentation**

## Conclusion

Ce repository de démonstration permet de tester le Proof Engine sur des cas réels avec des violations intentionnelles. Le système peut analyser, corriger et améliorer le code de manière automatique.
