"""
Obligations et vérifications pour le Proof Engine for Code v0.
Vérifie les obligations K: tests, lint, types, sécurité, complexité, docstring.
"""

import subprocess
import json
import os
from typing import Dict, Tuple
from proofengine.core.schemas import ObligationResults


def run_command(cmd: list[str], cwd: str, timeout: int = 30) -> Tuple[int, str, str]:
    """Exécute une commande et retourne le code de retour, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def check_tests(cwd: str) -> bool:
    """Vérifie que les tests passent."""
    returncode, stdout, stderr = run_command(["pytest", "-q"], cwd)
    return returncode == 0


def check_flake8(cwd: str) -> bool:
    """Vérifie le linting avec flake8."""
    returncode, stdout, stderr = run_command(["flake8", "."], cwd)
    return returncode == 0


def check_mypy(cwd: str) -> bool:
    """Vérifie les types avec mypy."""
    returncode, stdout, stderr = run_command(["mypy", "."], cwd)
    return returncode == 0


def check_bandit(cwd: str) -> bool:
    """Vérifie la sécurité avec bandit."""
    returncode, stdout, stderr = run_command(["bandit", "-q", "-r", "."], cwd)
    return returncode == 0


def check_complexity(cwd: str, max_cc: int = 10) -> bool:
    """Vérifie la complexité cyclomatique avec radon."""
    returncode, stdout, stderr = run_command(["radon", "cc", "-s", "-j", "."], cwd)
    
    if returncode != 0:
        return False
    
    try:
        data = json.loads(stdout or "{}")
        # Vérifier qu'aucune fonction n'a une complexité > max_cc
        for file_path, functions in data.items():
            for func in functions:
                if func.get("complexity", 0) > max_cc:
                    return False
        return True
    except (json.JSONDecodeError, KeyError):
        return False


def check_docstrings(cwd: str) -> bool:
    """Vérifie la présence de docstrings."""
    ok = True
    
    for root, dirs, files in os.walk(cwd):
        for filename in files:
            if filename.endswith(".py") and not filename.startswith("_"):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read().lstrip()
                        # Vérifier qu'il y a une docstring au niveau module
                        if not (content.startswith('"""') or content.startswith("'''")):
                            ok = False
                except Exception:
                    ok = False
    
    return ok


def evaluate_obligations(cwd: str) -> ObligationResults:
    """
    Évalue toutes les obligations sur un répertoire.
    
    Args:
        cwd: Répertoire de travail
        
    Returns:
        ObligationResults: Résultats des vérifications
    """
    return ObligationResults(
        tests_ok=check_tests(cwd),
        lint_ok=check_flake8(cwd),
        types_ok=check_mypy(cwd),
        security_ok=check_bandit(cwd),
        complexity_ok=check_complexity(cwd),
        docstring_ok=check_docstrings(cwd)
    )


def get_obligation_details(cwd: str) -> Dict[str, Any]:
    """
    Retourne les détails des vérifications d'obligations.
    
    Args:
        cwd: Répertoire de travail
        
    Returns:
        Dict avec les détails de chaque vérification
    """
    details = {}
    
    # Tests
    returncode, stdout, stderr = run_command(["pytest", "-v"], cwd)
    details["tests"] = {
        "passed": returncode == 0,
        "output": stdout,
        "errors": stderr
    }
    
    # Linting
    returncode, stdout, stderr = run_command(["flake8", "."], cwd)
    details["linting"] = {
        "passed": returncode == 0,
        "output": stdout,
        "errors": stderr
    }
    
    # Types
    returncode, stdout, stderr = run_command(["mypy", "."], cwd)
    details["types"] = {
        "passed": returncode == 0,
        "output": stdout,
        "errors": stderr
    }
    
    # Sécurité
    returncode, stdout, stderr = run_command(["bandit", "-q", "-r", "."], cwd)
    details["security"] = {
        "passed": returncode == 0,
        "output": stdout,
        "errors": stderr
    }
    
    # Complexité
    returncode, stdout, stderr = run_command(["radon", "cc", "-s", "-j", "."], cwd)
    details["complexity"] = {
        "passed": returncode == 0,
        "output": stdout,
        "errors": stderr
    }
    
    return details


def get_violation_summary(results: ObligationResults) -> Dict[str, Any]:
    """
    Retourne un résumé des violations.
    
    Args:
        results: Résultats des obligations
        
    Returns:
        Dict avec le résumé des violations
    """
    violations = []
    
    if not results.tests_ok:
        violations.append("tests_ok")
    if not results.lint_ok:
        violations.append("lint_ok")
    if not results.types_ok:
        violations.append("types_ok")
    if not results.security_ok:
        violations.append("security_ok")
    if not results.complexity_ok:
        violations.append("complexity_ok")
    if not results.docstring_ok:
        violations.append("docstring_ok")
    
    return {
        "total_violations": len(violations),
        "violations": violations,
        "all_passed": results.all_passed(),
        "success_rate": (6 - len(violations)) / 6
    }
