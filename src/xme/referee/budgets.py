"""
Budgets H/X pour la gouvernance bifocale.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class BudgetsHX:
    """Budgets pour les espaces H et X."""

    h_quota: int = 10
    x_quota: int = 20


class BudgetTracker:
    """Suivi des budgets H/X avec consommation et limites."""

    def __init__(self, budgets: BudgetsHX):
        self.budgets = budgets
        self.used: Dict[str, int] = {"H": 0, "X": 0}

    def remaining(self, space: str) -> int:
        """Retourne le budget restant pour un espace."""
        quota = self.budgets.h_quota if space == "H" else self.budgets.x_quota
        return max(0, quota - self.used.get(space, 0))

    def consume(self, space: str, units: int) -> bool:
        """Consomme des unités de budget. Retourne True si succès."""
        if self.remaining(space) < units:
            return False
        self.used[space] = self.used.get(space, 0) + units
        return True

    def report(self) -> Dict[str, int]:
        """Retourne un rapport des budgets utilisés et restants."""
        return {
            "H_used": self.used["H"],
            "H_remaining": self.remaining("H"),
            "X_used": self.used["X"],
            "X_remaining": self.remaining("X"),
        }
