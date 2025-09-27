"""Obligation checks used by deterministic controller tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from proofengine.core.schemas import ObligationResults


def _run_command_impl(command: List[str], cwd: str) -> Tuple[int, str, str]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def _resolve_runner() -> Callable[[List[str], str], Tuple[int, str, str]]:
    try:
        from controller import obligations as legacy  # type: ignore

        candidate = getattr(legacy, "run_command", None)
        if candidate is not None and candidate is not run_command:
            return candidate  # patched version supplied by tests
    except Exception:  # pragma: no cover - defensive
        pass
    return _run_command_impl


def run_command(command: List[str], cwd: str) -> Tuple[int, str, str]:
    runner = _resolve_runner()
    return runner(command, cwd)


def check_tests(cwd: str) -> bool:
    code, *_ = run_command(["pytest", "-q"], cwd)
    return code == 0


def check_flake8(cwd: str) -> bool:
    code, *_ = run_command(["flake8", "."], cwd)
    return code == 0


def check_mypy(cwd: str) -> bool:
    code, *_ = run_command(["mypy", ".", "--ignore-missing-imports"], cwd)
    return code == 0


def check_bandit(cwd: str) -> bool:
    code, *_ = run_command(["bandit", "-q", "-r", "."], cwd)
    return code == 0


def check_complexity(cwd: str, max_cc: int = 10) -> bool:
    code, stdout, _ = run_command(["radon", "cc", "-s", "-j", "."], cwd)
    if code != 0:
        return False
    try:
        payload = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        return False
    for functions in payload.values():
        for item in functions:
            if item.get("complexity", 0) > max_cc:
                return False
    return True


def check_docstrings(cwd: str) -> bool:
    for path in Path(cwd).rglob("*.py"):
        if path.name.startswith("_"):
            continue
        with path.open("r", encoding="utf-8") as handle:
            content = handle.read().lstrip()
            if not content.startswith('"""') and not content.startswith("'''"):
                return False
    return True


def evaluate_obligations(cwd: str) -> ObligationResults:
    return ObligationResults(
        tests_ok=check_tests(cwd),
        lint_ok=check_flake8(cwd),
        types_ok=check_mypy(cwd),
        security_ok=check_bandit(cwd),
        complexity_ok=check_complexity(cwd),
        docstring_ok=check_docstrings(cwd),
    )


def get_obligation_details(cwd: str) -> Dict[str, Dict[str, str]]:
    return {
        "tests": {"command": "pytest -q", "cwd": cwd},
        "lint": {"command": "flake8 .", "cwd": cwd},
        "types": {"command": "mypy .", "cwd": cwd},
        "security": {"command": "bandit -q -r .", "cwd": cwd},
        "complexity": {"command": "radon cc -s -j .", "cwd": cwd},
        "docstring": {"check": "static", "cwd": cwd},
    }


def get_violation_summary(results: ObligationResults) -> Dict[str, object]:
    violations = [name for name, ok in results.model_dump().items() if not ok]
    total = len(results.model_dump())
    passed = total - len(violations)
    return {
        "total_violations": len(violations),
        "violations": violations,
        "success_rate": passed / total if total else 0.0,
        "all_passed": len(violations) == 0,
    }
