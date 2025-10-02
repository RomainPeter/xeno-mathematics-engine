"""
Système de vérification unifié avec obligations S0/S1.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class Obligation:
    """Obligation de vérification."""

    id: str
    level: str  # S0, S1, S2
    check: Callable[[Dict[str, Any]], Tuple[bool, Dict[str, Any]]]
    description: str = ""

    def __post_init__(self):
        """Valide le niveau d'obligation."""
        if self.level not in ["S0", "S1", "S2"]:
            raise ValueError(f"Invalid obligation level: {self.level}")


@dataclass
class VerificationResult:
    """Résultat d'une vérification d'obligation."""

    obligation_id: str
    level: str
    ok: bool
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class VerificationReport:
    """Rapport de vérification."""

    version: int = 1
    when: datetime = None
    tool: str = "xme"
    results: List[VerificationResult] = None
    ok_all: bool = True

    def __post_init__(self):
        """Initialise les valeurs par défaut."""
        if self.when is None:
            self.when = datetime.now(timezone.utc)
        if self.results is None:
            self.results = []
        if self.results:
            self.ok_all = all(result.ok for result in self.results)


class Verifier:
    """Vérificateur unifié pour les obligations."""

    def __init__(self):
        self.obligations: Dict[str, Obligation] = {}

    def register_obligation(self, obligation: Obligation) -> None:
        """
        Enregistre une obligation.

        Args:
            obligation: Obligation à enregistrer
        """
        self.obligations[obligation.id] = obligation

    def register_obligations(self, obligations: List[Obligation]) -> None:
        """
        Enregistre plusieurs obligations.

        Args:
            obligations: Liste d'obligations à enregistrer
        """
        for obligation in obligations:
            self.register_obligation(obligation)

    def run(
        self, obligation_ids: List[str], payload: Dict[str, Any], level_filter: Optional[str] = None
    ) -> VerificationReport:
        """
        Exécute les vérifications d'obligations.

        Args:
            obligation_ids: IDs des obligations à vérifier
            payload: Données à vérifier
            level_filter: Filtre par niveau (optionnel)

        Returns:
            Rapport de vérification
        """
        results = []

        for obligation_id in obligation_ids:
            if obligation_id not in self.obligations:
                continue

            obligation = self.obligations[obligation_id]

            # Filtrer par niveau si spécifié
            if level_filter and obligation.level != level_filter:
                continue

            try:
                # Exécuter la vérification
                ok, details = obligation.check(payload)

                result = VerificationResult(
                    obligation_id=obligation_id,
                    level=obligation.level,
                    ok=ok,
                    details=details,
                    timestamp=datetime.now(timezone.utc),
                )
                results.append(result)

            except Exception as e:
                # En cas d'erreur, marquer comme échec
                result = VerificationResult(
                    obligation_id=obligation_id,
                    level=obligation.level,
                    ok=False,
                    details={"error": str(e)},
                    timestamp=datetime.now(timezone.utc),
                )
                results.append(result)

        # Créer le rapport
        report = VerificationReport(results=results, ok_all=all(result.ok for result in results))

        return report

    def run_by_level(self, payload: Dict[str, Any], level: str) -> VerificationReport:
        """
        Exécute toutes les obligations d'un niveau donné.

        Args:
            payload: Données à vérifier
            level: Niveau des obligations (S0, S1, S2)

        Returns:
            Rapport de vérification
        """
        obligation_ids = [
            id for id, obligation in self.obligations.items() if obligation.level == level
        ]

        return self.run(obligation_ids, payload, level)

    def get_obligations_by_level(self, level: str) -> List[Obligation]:
        """
        Retourne toutes les obligations d'un niveau donné.

        Args:
            level: Niveau des obligations

        Returns:
            Liste des obligations du niveau
        """
        return [obligation for obligation in self.obligations.values() if obligation.level == level]

    def get_all_obligations(self) -> List[Obligation]:
        """
        Retourne toutes les obligations enregistrées.

        Returns:
            Liste de toutes les obligations
        """
        return list(self.obligations.values())


def create_obligation(
    id: str,
    level: str,
    check_func: Callable[[Dict[str, Any]], Tuple[bool, Dict[str, Any]]],
    description: str = "",
) -> Obligation:
    """
    Crée une obligation.

    Args:
        id: Identifiant de l'obligation
        level: Niveau (S0, S1, S2)
        check_func: Fonction de vérification
        description: Description de l'obligation

    Returns:
        Obligation créée
    """
    return Obligation(id=id, level=level, check=check_func, description=description)
