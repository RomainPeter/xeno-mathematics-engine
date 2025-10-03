"""
Referee H/X - Gouvernance bifocale opérationnelle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from xme.adapters.logger import log_action
from xme.referee.alien_reserve import AlienReserve
from xme.referee.budgets import BudgetsHX, BudgetTracker
from xme.referee.pcn import SymbolStore


@dataclass
class RefereeConfig:
    """Configuration du Referee."""

    h_quota: int = 10
    x_quota: int = 20
    naming_charset: str = r"^[A-Za-z0-9_]+$"
    embargo_min_checks: list[str] = field(default_factory=list)  # e.g., ["psp:S1"]


def load_config(path: Path) -> RefereeConfig:
    """Charge la configuration depuis un fichier."""
    if not path.exists():
        return RefereeConfig()

    # Charger YAML
    import yaml  # type: ignore[import-untyped]

    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    return RefereeConfig(
        h_quota=cfg.get("budgets", {}).get("h_quota", 10),
        x_quota=cfg.get("budgets", {}).get("x_quota", 20),
        naming_charset=cfg.get("naming", {}).get("allowed_charset", r"^[A-Za-z0-9_]+$"),
        embargo_min_checks=cfg.get("embargo_rules", {}).get("min_checks", []),
    )


class Referee:
    """Referee principal pour la gouvernance H/X."""

    def __init__(self, cfg_path: Path, reserve_path: Path, symbols_path: Path):
        self.cfg = load_config(cfg_path)
        self.tracker = BudgetTracker(BudgetsHX(self.cfg.h_quota, self.cfg.x_quota))
        self.reserve = AlienReserve(reserve_path)
        self.symbols = SymbolStore(symbols_path)
        self._name_re = re.compile(self.cfg.naming_charset)

    def enforce_budgets(self, space: str, cost: int, pcap=None) -> bool:
        """Applique les budgets H/X."""
        ok = self.tracker.consume(space, cost)
        if pcap:
            log_action(
                pcap, action="referee.budget_consume", obligations={f"budget.{space}": str(ok)}
            )
        return ok

    def gate_baptism(
        self, lineage_id: str, concept_id: str, symbol: str, proof_ref: str | None, pcap=None
    ) -> Dict[str, Any]:
        """Contrôle l'accès au baptême de symboles."""
        # Vérifier le charset du nom
        if not self._name_re.match(symbol or ""):
            if pcap:
                log_action(
                    pcap, action="symbol.baptize.reject", obligations={"name.charset": "false"}
                )
            return {"ok": False, "reason": "invalid_symbol_charset"}

        # Vérifier l'embargo
        if self.reserve.is_embargoed(lineage_id):
            if pcap:
                log_action(
                    pcap, action="symbol.baptize.reject", obligations={"alien_reserve": "embargoed"}
                )
            return {"ok": False, "reason": "embargoed"}

        # Vérifier la preuve
        if not proof_ref:
            if pcap:
                log_action(
                    pcap,
                    action="symbol.baptize.reject",
                    obligations={"pcn.proof_ref:exists": "false"},
                )
            return {"ok": False, "reason": "missing_proof_ref"}

        # Baptême autorisé
        entry = self.symbols.propose(concept_id=concept_id, symbol=symbol, proof_ref=proof_ref)
        if pcap:
            log_action(
                pcap,
                action="symbol.baptize.accept",
                obligations={"pcn.proof_ref:exists": "true"},
                psp_ref=proof_ref,
            )
        return {"ok": True, "entry": entry.model_dump()}

    def status(self) -> Dict[str, Any]:
        """Retourne le statut complet du Referee."""
        return {
            "budgets": self.tracker.report(),
            "reserves": self.reserve.list(),
            "symbols": [s.model_dump() for s in self.symbols.list()],
        }
