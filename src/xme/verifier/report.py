"""
Système de rapport de vérification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

import orjson


@dataclass
class Report:
    """Rapport de vérification JSON."""

    version: int = 1
    when: datetime = None
    tool: str = "xme"
    results: List[Dict[str, Any]] = None
    ok_all: bool = True

    def __post_init__(self):
        """Initialise les valeurs par défaut."""
        if self.when is None:
            self.when = datetime.now(timezone.utc)
        if self.results is None:
            self.results = []
        if self.results:
            self.ok_all = all(result.get("ok", False) for result in self.results)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le rapport en dictionnaire."""
        return {
            "version": self.version,
            "when": self.when.isoformat(),
            "tool": self.tool,
            "results": self.results,
            "ok_all": self.ok_all,
        }

    def to_json(self) -> str:
        """Sérialise le rapport en JSON."""
        return orjson.dumps(self.to_dict(), option=orjson.OPT_INDENT_2).decode()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Report":
        """Crée un rapport à partir d'un dictionnaire."""
        # Convertir la date ISO en datetime
        when_str = data.get("when")
        if when_str:
            when = datetime.fromisoformat(when_str.replace("Z", "+00:00"))
        else:
            when = datetime.now(timezone.utc)

        return cls(
            version=data.get("version", 1),
            when=when,
            tool=data.get("tool", "xme"),
            results=data.get("results", []),
            ok_all=data.get("ok_all", True),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Report":
        """Crée un rapport à partir d'une chaîne JSON."""
        data = orjson.loads(json_str)
        return cls.from_dict(data)

    def add_result(self, obligation_id: str, level: str, ok: bool, details: Dict[str, Any]) -> None:
        """Ajoute un résultat de vérification."""
        result = {
            "obligation_id": obligation_id,
            "level": level,
            "ok": ok,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.results.append(result)
        # Mettre à jour ok_all
        self.ok_all = all(result.get("ok", False) for result in self.results)

    def get_results_by_level(self, level: str) -> List[Dict[str, Any]]:
        """Retourne les résultats d'un niveau donné."""
        return [result for result in self.results if result.get("level") == level]

    def get_failed_results(self) -> List[Dict[str, Any]]:
        """Retourne les résultats échoués."""
        return [result for result in self.results if not result.get("ok", False)]

    def get_passed_results(self) -> List[Dict[str, Any]]:
        """Retourne les résultats réussis."""
        return [result for result in self.results if result.get("ok", False)]

    def summary(self) -> Dict[str, Any]:
        """Retourne un résumé du rapport."""
        total = len(self.results)
        passed = len(self.get_passed_results())
        failed = len(self.get_failed_results())

        # Compter par niveau
        by_level = {}
        for result in self.results:
            level = result.get("level", "unknown")
            if level not in by_level:
                by_level[level] = {"total": 0, "passed": 0, "failed": 0}
            by_level[level]["total"] += 1
            if result.get("ok", False):
                by_level[level]["passed"] += 1
            else:
                by_level[level]["failed"] += 1

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "ok_all": self.ok_all,
            "by_level": by_level,
        }


def create_report(results: List[Dict[str, Any]]) -> Report:
    """
    Crée un rapport à partir d'une liste de résultats.

    Args:
        results: Liste des résultats de vérification

    Returns:
        Rapport créé
    """
    report = Report()
    for result in results:
        report.add_result(
            obligation_id=result.get("obligation_id", ""),
            level=result.get("level", ""),
            ok=result.get("ok", False),
            details=result.get("details", {}),
        )
    return report


def merge_reports(reports: List[Report]) -> Report:
    """
    Fusionne plusieurs rapports en un seul.

    Args:
        reports: Liste des rapports à fusionner

    Returns:
        Rapport fusionné
    """
    merged = Report()

    for report in reports:
        for result in report.results:
            merged.add_result(
                obligation_id=result.get("obligation_id", ""),
                level=result.get("level", ""),
                ok=result.get("ok", False),
                details=result.get("details", {}),
            )

    return merged


def save_report(report: Report, filepath: str) -> None:
    """
    Sauvegarde un rapport dans un fichier.

    Args:
        report: Rapport à sauvegarder
        filepath: Chemin du fichier
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report.to_json())


def load_report(filepath: str) -> Report:
    """
    Charge un rapport depuis un fichier.

    Args:
        filepath: Chemin du fichier

    Returns:
        Rapport chargé
    """
    with open(filepath, "r", encoding="utf-8") as f:
        json_str = f.read()
    return Report.from_json(json_str)
