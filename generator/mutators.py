"""
Mutateurs pour la génération stochastique d'actions.
Applique des transformations sur le code pour générer des variantes.
"""

import random
import re
from typing import Any, Dict, List, Optional, Tuple
from ..core.schemas import ActionVariant, VJustification


class CodeMutator:
    """Mutateur de code pour générer des variantes d'actions."""
    
    def __init__(self, seed: int = None):
        """Initialise le mutateur avec une graine."""
        if seed is not None:
            random.seed(seed)
        self.seed = seed
    
    def add_docstring(self, code: str, function_name: str = None) -> str:
        """Ajoute une docstring à une fonction."""
        if function_name:
            # Ajouter docstring à une fonction spécifique
            pattern = rf'def {function_name}\([^)]*\):'
            replacement = f'def {function_name}(...):\n    """Documentation de {function_name}."""'
            return re.sub(pattern, replacement, code)
        else:
            # Ajouter docstring à la première fonction trouvée
            pattern = r'(def \w+\([^)]*\):)'
            replacement = r'\1\n    """Documentation de la fonction."""'
            return re.sub(pattern, replacement, code, count=1)
    
    def add_type_hints(self, code: str) -> str:
        """Ajoute des annotations de type."""
        # Ajouter des annotations de type basiques
        type_hints = {
            'str': 'str',
            'int': 'int',
            'float': 'float',
            'bool': 'bool',
            'list': 'List[str]',
            'dict': 'Dict[str, Any]'
        }
        
        # Remplacer les paramètres sans type
        for param_type, hint in type_hints.items():
            pattern = rf'(\w+): {param_type}'
            replacement = rf'\1: {hint}'
            code = re.sub(pattern, replacement, code)
        
        return code
    
    def sanitize_regex(self, code: str) -> str:
        """Ajoute la sanitisation des entrées regex."""
        # Ajouter des vérifications de sécurité
        security_checks = [
            'import re\n',
            'def sanitize_input(text: str) -> str:\n',
            '    """Sanitise l\'entrée pour éviter les injections."""\n',
            '    return re.escape(text)\n\n'
        ]
        
        return ''.join(security_checks) + code
    
    def throttle_wrapper(self, code: str, function_name: str = None) -> str:
        """Ajoute un wrapper de limitation de débit."""
        if not function_name:
            # Trouver la première fonction
            match = re.search(r'def (\w+)\(', code)
            if match:
                function_name = match.group(1)
            else:
                return code
        
        # Ajouter le décorateur de limitation
        decorator = f'@throttle(rate=10, per=60)  # 10 appels par minute\n'
        pattern = rf'(def {function_name}\([^)]*\):)'
        replacement = decorator + r'\1'
        
        return re.sub(pattern, replacement, code)
    
    def pure_refactor(self, code: str) -> str:
        """Refactorise le code pour le rendre plus pur."""
        # Remplacer les print par des return
        code = re.sub(r'print\(([^)]+)\)', r'return \1', code)
        
        # Ajouter des annotations de type
        code = self.add_type_hints(code)
        
        # Ajouter des docstrings
        code = self.add_docstring(code)
        
        return code
    
    def add_error_handling(self, code: str) -> str:
        """Ajoute la gestion d'erreurs."""
        # Ajouter try/except autour des opérations risquées
        risky_operations = ['open', 'eval', 'exec', 'compile']
        
        for op in risky_operations:
            pattern = rf'(\s*)({op}\([^)]+\))'
            replacement = rf'\1try:\n\1    \2\nexcept Exception as e:\n\1    raise ValueError(f"Erreur {op}: {{e}}")'
            code = re.sub(pattern, replacement, code)
        
        return code
    
    def add_validation(self, code: str) -> str:
        """Ajoute la validation des entrées."""
        # Ajouter des vérifications de type
        validation_code = '''
def validate_input(value, expected_type):
    """Valide le type d'entrée."""
    if not isinstance(value, expected_type):
        raise TypeError(f"Type attendu: {expected_type}, reçu: {type(value)}")
    return value

'''
        return validation_code + code
    
    def add_logging(self, code: str) -> str:
        """Ajoute la journalisation."""
        # Ajouter des logs
        logging_code = '''
import logging
logger = logging.getLogger(__name__)

'''
        # Ajouter des logs dans les fonctions
        pattern = r'(def \w+\([^)]*\):)'
        replacement = r'\1\n    logger.info(f"Exécution de {__name__}")'
        code = re.sub(pattern, replacement, code)
        
        return logging_code + code


class ActionGenerator:
    """Générateur d'actions avec mutateurs."""
    
    def __init__(self, seed: int = None):
        """Initialise le générateur."""
        self.mutator = CodeMutator(seed)
        self.seed = seed
    
    def propose_actions(self, goal: str, obligations: List[Dict[str, Any]], 
                       seed: int = None, k: int = 3) -> List[ActionVariant]:
        """
        Propose k variantes d'actions pour atteindre un objectif.
        """
        if seed is not None:
            random.seed(seed)
        
        variants = []
        
        # Générer des variantes basées sur l'objectif
        if "sanitize" in goal.lower():
            variants.extend(self._generate_sanitize_variants(goal, obligations, k))
        elif "rate" in goal.lower() or "limit" in goal.lower():
            variants.extend(self._generate_rate_limit_variants(goal, obligations, k))
        elif "pure" in goal.lower():
            variants.extend(self._generate_pure_variants(goal, obligations, k))
        else:
            variants.extend(self._generate_generic_variants(goal, obligations, k))
        
        return variants[:k]
    
    def _generate_sanitize_variants(self, goal: str, obligations: List[Dict[str, Any]], k: int) -> List[ActionVariant]:
        """Génère des variantes pour la sanitisation."""
        variants = []
        
        # Variante 1: Sanitisation regex
        variants.append(ActionVariant(
            action_id="sanitize_regex",
            description="Ajouter la sanitisation regex des entrées",
            patch=self.mutator.sanitize_regex(""),
            meta={"approach": "regex", "security": "high"},
            estimated_cost=VJustification(time_ms=100, retries=0, backtracks=0, audit_cost=0.5, risk=0.2, tech_debt=0),
            confidence=0.8
        ))
        
        # Variante 2: Validation de type
        variants.append(ActionVariant(
            action_id="validate_types",
            description="Ajouter la validation des types d'entrée",
            patch=self.mutator.add_validation(""),
            meta={"approach": "validation", "security": "medium"},
            estimated_cost=VJustification(time_ms=80, retries=0, backtracks=0, audit_cost=0.3, risk=0.1, tech_debt=0),
            confidence=0.9
        ))
        
        # Variante 3: Gestion d'erreurs
        variants.append(ActionVariant(
            action_id="error_handling",
            description="Ajouter la gestion d'erreurs robuste",
            patch=self.mutator.add_error_handling(""),
            meta={"approach": "error_handling", "security": "high"},
            estimated_cost=VJustification(time_ms=120, retries=0, backtracks=0, audit_cost=0.7, risk=0.3, tech_debt=0),
            confidence=0.7
        ))
        
        return variants
    
    def _generate_rate_limit_variants(self, goal: str, obligations: List[Dict[str, Any]], k: int) -> List[ActionVariant]:
        """Génère des variantes pour la limitation de débit."""
        variants = []
        
        # Variante 1: Décorateur de limitation
        variants.append(ActionVariant(
            action_id="throttle_decorator",
            description="Ajouter un décorateur de limitation de débit",
            patch=self.mutator.throttle_wrapper(""),
            meta={"approach": "decorator", "performance": "high"},
            estimated_cost=VJustification(time_ms=90, retries=0, backtracks=0, audit_cost=0.4, risk=0.2, tech_debt=0),
            confidence=0.8
        ))
        
        # Variante 2: Limitation par token
        variants.append(ActionVariant(
            action_id="token_bucket",
            description="Implémenter un bucket de tokens",
            patch="class TokenBucket:\n    def __init__(self, capacity, refill_rate):\n        self.capacity = capacity\n        self.tokens = capacity\n        self.refill_rate = refill_rate\n        self.last_refill = time.time()\n    \n    def consume(self, tokens=1):\n        if self.tokens >= tokens:\n            self.tokens -= tokens\n            return True\n        return False",
            meta={"approach": "token_bucket", "performance": "medium"},
            estimated_cost=VJustification(time_ms=150, retries=0, backtracks=0, audit_cost=0.6, risk=0.3, tech_debt=0),
            confidence=0.6
        ))
        
        return variants
    
    def _generate_pure_variants(self, goal: str, obligations: List[Dict[str, Any]], k: int) -> List[ActionVariant]:
        """Génère des variantes pour les fonctions pures."""
        variants = []
        
        # Variante 1: Refactorisation pure
        variants.append(ActionVariant(
            action_id="pure_refactor",
            description="Refactoriser en fonction pure",
            patch=self.mutator.pure_refactor(""),
            meta={"approach": "pure", "functional": "high"},
            estimated_cost=VJustification(time_ms=110, retries=0, backtracks=0, audit_cost=0.5, risk=0.1, tech_debt=0),
            confidence=0.9
        ))
        
        # Variante 2: Ajout d'annotations de type
        variants.append(ActionVariant(
            action_id="type_annotations",
            description="Ajouter des annotations de type complètes",
            patch=self.mutator.add_type_hints(""),
            meta={"approach": "typing", "functional": "medium"},
            estimated_cost=VJustification(time_ms=70, retries=0, backtracks=0, audit_cost=0.2, risk=0.1, tech_debt=0),
            confidence=0.8
        ))
        
        return variants
    
    def _generate_generic_variants(self, goal: str, obligations: List[Dict[str, Any]], k: int) -> List[ActionVariant]:
        """Génère des variantes génériques."""
        variants = []
        
        # Variante 1: Ajout de docstring
        variants.append(ActionVariant(
            action_id="add_docstring",
            description="Ajouter une docstring",
            patch=self.mutator.add_docstring(""),
            meta={"approach": "documentation", "quality": "high"},
            estimated_cost=VJustification(time_ms=50, retries=0, backtracks=0, audit_cost=0.1, risk=0.1, tech_debt=0),
            confidence=0.9
        ))
        
        # Variante 2: Ajout de logging
        variants.append(ActionVariant(
            action_id="add_logging",
            description="Ajouter la journalisation",
            patch=self.mutator.add_logging(""),
            meta={"approach": "logging", "observability": "high"},
            estimated_cost=VJustification(time_ms=80, retries=0, backtracks=0, audit_cost=0.3, risk=0.2, tech_debt=0),
            confidence=0.7
        ))
        
        return variants
