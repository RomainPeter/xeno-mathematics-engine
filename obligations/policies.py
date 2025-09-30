"""
Système de politiques et d'obligations pour la vérification déterministe.
Implémente les vérifications: pytest, ruff, mypy, radon, etc.
"""

import ast
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Tuple

from proofengine.core.schemas import Proof, VJustification


class PolicyEngine:
    """Moteur de politiques pour la vérification des obligations."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialise le moteur avec une configuration."""
        self.config = config or {}
        self.policies = {}
        self._register_default_policies()

    def _register_default_policies(self):
        """Enregistre les politiques par défaut."""
        self.policies = {
            "pytest": self._run_pytest,
            "ruff": self._run_ruff,
            "mypy": self._run_mypy,
            "forbidden_imports": self._check_forbidden_imports,
            "cyclomatic_complexity": self._check_cyclomatic_complexity,
            "docstring": self._check_docstring,
            "type_hints": self._check_type_hints,
            "pure_function": self._check_pure_function,
        }

    def check_obligations(self, context: Dict[str, Any]) -> Tuple[List[Proof], VJustification]:
        """
        Vérifie toutes les obligations applicables.
        Retourne les preuves et le coût total.
        """
        proofs = []
        total_cost = VJustification()

        for obligation in context.get("obligations", []):
            policy_name = obligation.get("policy")
            if policy_name not in self.policies:
                continue

            try:
                proof, cost = self.policies[policy_name](context, obligation)
                proofs.append(proof)
                total_cost.time_ms += cost.time_ms
                total_cost.retries += cost.retries
                total_cost.audit_cost += cost.audit_cost
                total_cost.risk += cost.risk
                total_cost.tech_debt += cost.tech_debt
            except Exception as e:
                # En cas d'erreur, créer une preuve d'échec
                proofs.append(
                    Proof(
                        kind="policy",
                        name=policy_name,
                        passed=False,
                        logs=f"Erreur: {str(e)}",
                        artifacts=[],
                    )
                )
                total_cost.audit_cost += 1.0

        return proofs, total_cost

    def _run_pytest(
        self, context: Dict[str, Any], obligation: Dict[str, Any]
    ) -> Tuple[Proof, VJustification]:
        """Exécute pytest sur les tests."""
        start_time = self._get_time_ms()

        try:
            # Créer un fichier temporaire pour les tests
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                test_content = context.get("test_content", "")
                f.write(test_content)
                test_file = f.name

            # Exécuter pytest
            result = subprocess.run(
                ["python", "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Nettoyer
            os.unlink(test_file)

            passed = result.returncode == 0
            logs = f"stdout: {result.stdout}\nstderr: {result.stderr}"

            return (
                Proof(
                    kind="unit",
                    name="pytest",
                    passed=passed,
                    logs=logs,
                    artifacts=[test_file],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=0,
                    backtracks=0,
                    audit_cost=1.0 if passed else 2.0,
                    risk=0.1 if passed else 0.5,
                    tech_debt=0,
                ),
            )

        except Exception as e:
            return (
                Proof(
                    kind="unit",
                    name="pytest",
                    passed=False,
                    logs=f"Erreur pytest: {str(e)}",
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=1,
                    backtracks=0,
                    audit_cost=3.0,
                    risk=0.8,
                    tech_debt=1,
                ),
            )

    def _run_ruff(
        self, context: Dict[str, Any], obligation: Dict[str, Any]
    ) -> Tuple[Proof, VJustification]:
        """Exécute ruff pour la vérification de style."""
        start_time = self._get_time_ms()

        try:
            # Créer un fichier temporaire pour le code
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                code_content = context.get("code_content", "")
                f.write(code_content)
                code_file = f.name

            # Exécuter ruff
            result = subprocess.run(
                ["ruff", "check", code_file], capture_output=True, text=True, timeout=10
            )

            # Nettoyer
            os.unlink(code_file)

            passed = result.returncode == 0
            logs = f"stdout: {result.stdout}\nstderr: {result.stderr}"

            return (
                Proof(
                    kind="static",
                    name="ruff",
                    passed=passed,
                    logs=logs,
                    artifacts=[code_file],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=0,
                    backtracks=0,
                    audit_cost=0.5 if passed else 1.0,
                    risk=0.1 if passed else 0.3,
                    tech_debt=0,
                ),
            )

        except Exception as e:
            return (
                Proof(
                    kind="static",
                    name="ruff",
                    passed=False,
                    logs=f"Erreur ruff: {str(e)}",
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=1,
                    backtracks=0,
                    audit_cost=2.0,
                    risk=0.5,
                    tech_debt=1,
                ),
            )

    def _run_mypy(
        self, context: Dict[str, Any], obligation: Dict[str, Any]
    ) -> Tuple[Proof, VJustification]:
        """Exécute mypy pour la vérification de types."""
        start_time = self._get_time_ms()

        try:
            # Créer un fichier temporaire pour le code
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                code_content = context.get("code_content", "")
                f.write(code_content)
                code_file = f.name

            # Exécuter mypy
            result = subprocess.run(
                ["mypy", code_file, "--ignore-missing-imports"],
                capture_output=True,
                text=True,
                timeout=15,
            )

            # Nettoyer
            os.unlink(code_file)

            passed = result.returncode == 0
            logs = f"stdout: {result.stdout}\nstderr: {result.stderr}"

            return (
                Proof(
                    kind="static",
                    name="mypy",
                    passed=passed,
                    logs=logs,
                    artifacts=[code_file],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=0,
                    backtracks=0,
                    audit_cost=1.0 if passed else 2.0,
                    risk=0.1 if passed else 0.4,
                    tech_debt=0,
                ),
            )

        except Exception as e:
            return (
                Proof(
                    kind="static",
                    name="mypy",
                    passed=False,
                    logs=f"Erreur mypy: {str(e)}",
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=1,
                    backtracks=0,
                    audit_cost=2.5,
                    risk=0.6,
                    tech_debt=1,
                ),
            )

    def _check_forbidden_imports(
        self, context: Dict[str, Any], obligation: Dict[str, Any]
    ) -> Tuple[Proof, VJustification]:
        """Vérifie les imports interdits."""
        start_time = self._get_time_ms()

        try:
            code_content = context.get("code_content", "")
            forbidden_imports = obligation.get("forbidden_imports", ["eval", "exec", "compile"])

            # Analyser le code avec AST
            tree = ast.parse(code_content)
            violations = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in forbidden_imports:
                            violations.append(f"Import interdit: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module in forbidden_imports:
                        violations.append(f"Import interdit: {node.module}")

            passed = len(violations) == 0
            logs = f"Violations trouvées: {violations}" if violations else "Aucune violation"

            return (
                Proof(
                    kind="policy",
                    name="forbidden_imports",
                    passed=passed,
                    logs=logs,
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=0,
                    backtracks=0,
                    audit_cost=0.2 if passed else 0.5,
                    risk=0.1 if passed else 0.7,
                    tech_debt=0,
                ),
            )

        except Exception as e:
            return (
                Proof(
                    kind="policy",
                    name="forbidden_imports",
                    passed=False,
                    logs=f"Erreur analyse: {str(e)}",
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=1,
                    backtracks=0,
                    audit_cost=1.0,
                    risk=0.8,
                    tech_debt=1,
                ),
            )

    def _check_cyclomatic_complexity(
        self, context: Dict[str, Any], obligation: Dict[str, Any]
    ) -> Tuple[Proof, VJustification]:
        """Vérifie la complexité cyclomatique."""
        start_time = self._get_time_ms()

        try:
            code_content = context.get("code_content", "")
            max_complexity = obligation.get("max_complexity", 10)

            # Calculer la complexité cyclomatique (version simplifiée)
            complexity = self._calculate_cyclomatic_complexity(code_content)

            passed = complexity <= max_complexity
            logs = f"Complexité: {complexity}, Limite: {max_complexity}"

            return (
                Proof(
                    kind="static",
                    name="cyclomatic_complexity",
                    passed=passed,
                    logs=logs,
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=0,
                    backtracks=0,
                    audit_cost=0.3 if passed else 0.8,
                    risk=0.1 if passed else 0.4,
                    tech_debt=0 if passed else 1,
                ),
            )

        except Exception as e:
            return (
                Proof(
                    kind="static",
                    name="cyclomatic_complexity",
                    passed=False,
                    logs=f"Erreur calcul: {str(e)}",
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=1,
                    backtracks=0,
                    audit_cost=1.0,
                    risk=0.6,
                    tech_debt=1,
                ),
            )

    def _check_docstring(
        self, context: Dict[str, Any], obligation: Dict[str, Any]
    ) -> Tuple[Proof, VJustification]:
        """Vérifie la présence de docstrings."""
        start_time = self._get_time_ms()

        try:
            code_content = context.get("code_content", "")

            # Analyser le code avec AST
            tree = ast.parse(code_content)
            missing_docstrings = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(node):
                        missing_docstrings.append(node.name)

            passed = len(missing_docstrings) == 0
            logs = (
                f"Fonctions sans docstring: {missing_docstrings}"
                if missing_docstrings
                else "Toutes les fonctions ont une docstring"
            )

            return (
                Proof(
                    kind="policy",
                    name="docstring",
                    passed=passed,
                    logs=logs,
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=0,
                    backtracks=0,
                    audit_cost=0.1 if passed else 0.3,
                    risk=0.1 if passed else 0.2,
                    tech_debt=0,
                ),
            )

        except Exception as e:
            return (
                Proof(
                    kind="policy",
                    name="docstring",
                    passed=False,
                    logs=f"Erreur analyse: {str(e)}",
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=1,
                    backtracks=0,
                    audit_cost=0.5,
                    risk=0.3,
                    tech_debt=0,
                ),
            )

    def _check_type_hints(
        self, context: Dict[str, Any], obligation: Dict[str, Any]
    ) -> Tuple[Proof, VJustification]:
        """Vérifie la présence d'annotations de type."""
        start_time = self._get_time_ms()

        try:
            code_content = context.get("code_content", "")

            # Analyser le code avec AST
            tree = ast.parse(code_content)
            missing_hints = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.returns and not all(arg.annotation for arg in node.args.args):
                        missing_hints.append(node.name)

            passed = len(missing_hints) == 0
            logs = (
                f"Fonctions sans annotations: {missing_hints}"
                if missing_hints
                else "Toutes les fonctions ont des annotations"
            )

            return (
                Proof(
                    kind="policy",
                    name="type_hints",
                    passed=passed,
                    logs=logs,
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=0,
                    backtracks=0,
                    audit_cost=0.1 if passed else 0.2,
                    risk=0.1 if passed else 0.2,
                    tech_debt=0,
                ),
            )

        except Exception as e:
            return (
                Proof(
                    kind="policy",
                    name="type_hints",
                    passed=False,
                    logs=f"Erreur analyse: {str(e)}",
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=1,
                    backtracks=0,
                    audit_cost=0.3,
                    risk=0.2,
                    tech_debt=0,
                ),
            )

    def _check_pure_function(
        self, context: Dict[str, Any], obligation: Dict[str, Any]
    ) -> Tuple[Proof, VJustification]:
        """Vérifie qu'une fonction est pure (pas d'effets de bord)."""
        start_time = self._get_time_ms()

        try:
            code_content = context.get("code_content", "")

            # Analyser le code avec AST
            tree = ast.parse(code_content)
            side_effects = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ["print", "input", "open", "file"]:
                            side_effects.append(f"Appel avec effet de bord: {node.func.id}")
                elif isinstance(node, ast.Assign):
                    # Vérifier les assignations à des variables globales
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            side_effects.append(f"Assignation: {target.id}")

            passed = len(side_effects) == 0
            logs = f"Effets de bord détectés: {side_effects}" if side_effects else "Fonction pure"

            return (
                Proof(
                    kind="property",
                    name="pure_function",
                    passed=passed,
                    logs=logs,
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=0,
                    backtracks=0,
                    audit_cost=0.2 if passed else 0.5,
                    risk=0.1 if passed else 0.3,
                    tech_debt=0,
                ),
            )

        except Exception as e:
            return (
                Proof(
                    kind="property",
                    name="pure_function",
                    passed=False,
                    logs=f"Erreur analyse: {str(e)}",
                    artifacts=[],
                ),
                VJustification(
                    time_ms=self._get_time_ms() - start_time,
                    retries=1,
                    backtracks=0,
                    audit_cost=0.5,
                    risk=0.4,
                    tech_debt=0,
                ),
            )

    def _calculate_cyclomatic_complexity(self, code: str) -> int:
        """Calcule la complexité cyclomatique (version simplifiée)."""
        complexity = 1  # Base complexity

        # Compter les structures de contrôle
        control_structures = [
            "if",
            "elif",
            "else",
            "for",
            "while",
            "try",
            "except",
            "finally",
            "with",
            "and",
            "or",
            "assert",
            "break",
            "continue",
            "return",
        ]

        for structure in control_structures:
            complexity += code.count(f" {structure} ")
            complexity += code.count(f"{structure}(")
            complexity += code.count(f"{structure}:")

        return complexity

    def _get_time_ms(self) -> int:
        """Retourne le temps actuel en millisecondes."""
        import time

        return int(time.time() * 1000)
