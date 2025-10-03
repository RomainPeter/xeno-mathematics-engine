"""
Scheduler avec boucle discovery utilisant bandit ε-greedy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import orjson

from xme.adapters.logger import log_action
from xme.orchestrator.event_bus import EventBus
from xme.orchestrator.loops.ae import run_ae
from xme.orchestrator.loops.cegis import run_cegis
from xme.orchestrator.state import Budgets, RunState
from xme.pcap.store import PCAPStore
from xme.selection.bandit import EpsilonGreedy


class DiscoveryConfig:
    """Configuration pour la boucle discovery."""

    def __init__(
        self,
        turns: int,
        ae_context: str,
        cegis_secret: str,
        ae_budget_ms: int = 1500,
        cegis_budget_ms: int = 5000,
        cegis_max_iters: int = 16,
        epsilon: float = 0.1,
    ):
        self.turns = turns
        self.ae_context = ae_context
        self.cegis_secret = cegis_secret
        self.ae_budget_ms = ae_budget_ms
        self.cegis_budget_ms = cegis_budget_ms
        self.cegis_max_iters = cegis_max_iters
        self.epsilon = epsilon


class DiscoveryScheduler:
    """Scheduler pour la boucle discovery."""

    def __init__(self, config: DiscoveryConfig):
        self.config = config
        self.bandit = EpsilonGreedy(["ae", "cegis"], epsilon=config.epsilon)
        self.turn_results: List[Dict[str, Any]] = []

    async def run_discovery(
        self, state: RunState, bus: EventBus, store: PCAPStore, out_dir: Path
    ) -> Dict[str, Any]:
        """
        Exécute la boucle discovery.

        Args:
            state: État de l'exécution
            bus: Bus d'événements
            store: Store PCAP pour le logging
            out_dir: Répertoire de sortie pour les résultats

        Returns:
            Résultats de la boucle discovery
        """
        out_dir.mkdir(parents=True, exist_ok=True)

        # Log du début de discovery
        log_action(
            store,
            action="discovery_start",
            level="S0",
            obligations={"turns": str(self.config.turns), "epsilon": str(self.config.epsilon)},
        )

        for turn in range(self.config.turns):
            # Sélection d'arme
            selected_arm = self.bandit.select()

            # Log de la sélection
            log_action(
                store,
                action="discovery_select",
                level="S0",
                obligations={"turn": str(turn + 1), "arm": selected_arm},
            )

            # Exécution de l'arme sélectionnée
            turn_result = await self._execute_arm(selected_arm, turn, state, bus, store, out_dir)

            # Calcul de la récompense
            reward = self._calculate_reward(selected_arm, turn_result)

            # Mise à jour du bandit
            self.bandit.update(selected_arm, reward)

            # Stockage du résultat
            turn_result.update({"turn": turn + 1, "arm": selected_arm, "reward": reward})
            self.turn_results.append(turn_result)

            # Log de la récompense
            log_action(
                store,
                action="discovery_reward",
                level="S0",
                obligations={"arm": selected_arm, "reward": str(reward)},
            )

        # Log de fin
        log_action(
            store,
            action="discovery_done",
            level="S0",
            obligations={"total_turns": str(self.config.turns)},
        )

        # Résultats finaux
        final_stats = self.bandit.get_stats()
        best_arm = self.bandit.get_best_arm()

        return {
            "config": {
                "turns": self.config.turns,
                "epsilon": self.config.epsilon,
                "ae_context": self.config.ae_context,
                "cegis_secret": self.config.cegis_secret,
            },
            "results": self.turn_results,
            "final_stats": final_stats,
            "best_arm": best_arm,
            "total_reward": sum(result["reward"] for result in self.turn_results),
        }

    async def _execute_arm(
        self, arm: str, turn: int, state: RunState, bus: EventBus, store: PCAPStore, out_dir: Path
    ) -> Dict[str, Any]:
        """Exécute l'arme sélectionnée."""
        if arm == "ae":
            return await self._execute_ae(turn, state, bus, store, out_dir)
        elif arm == "cegis":
            return await self._execute_cegis(turn, state, bus, store, out_dir)
        else:
            raise ValueError(f"Unknown arm: {arm}")

    async def _execute_ae(
        self, turn: int, state: RunState, bus: EventBus, store: PCAPStore, out_dir: Path
    ) -> Dict[str, Any]:
        """Exécute AE pour un tour."""
        out_psp = out_dir / f"ae_turn_{turn + 1}.json"

        # Créer un état temporaire pour AE
        ae_state = RunState(
            run_id=f"{state.run_id}_ae_turn_{turn + 1}",
            budgets=Budgets(ae_ms=self.config.ae_budget_ms),
        )

        try:
            await run_ae(self.config.ae_context, ae_state, bus, store, out_psp)

            # Lire le PSP généré pour calculer la récompense
            psp_data = orjson.loads(out_psp.read_bytes())
            n_edges = len(psp_data.get("edges", []))
            n_blocks = len(psp_data.get("blocks", []))

            return {
                "success": True,
                "output_file": str(out_psp),
                "n_edges": n_edges,
                "n_blocks": n_blocks,
                "events": [],  # TODO: extraire les événements du bus
            }
        except Exception as e:
            return {"success": False, "error": str(e), "events": []}

    async def _execute_cegis(
        self, turn: int, state: RunState, bus: EventBus, store: PCAPStore, out_dir: Path
    ) -> Dict[str, Any]:
        """Exécute CEGIS pour un tour."""
        out_result = out_dir / f"cegis_turn_{turn + 1}.json"

        # Créer un état temporaire pour CEGIS
        cegis_state = RunState(
            run_id=f"{state.run_id}_cegis_turn_{turn + 1}",
            budgets=Budgets(cegis_ms=self.config.cegis_budget_ms),
        )

        try:
            await run_cegis(
                self.config.cegis_secret,
                self.config.cegis_max_iters,
                cegis_state,
                bus,
                store,
                out_result,
            )

            # Lire le résultat CEGIS
            result_data = orjson.loads(out_result.read_bytes())
            iters = result_data.get("iters", 0)
            ok = result_data.get("ok", False)

            return {
                "success": True,
                "output_file": str(out_result),
                "iters": iters,
                "ok": ok,
                "events": [],  # TODO: extraire les événements du bus
            }
        except Exception as e:
            return {"success": False, "error": str(e), "events": []}

    def _calculate_reward(self, arm: str, result: Dict[str, Any]) -> float:
        """Calcule la récompense pour un résultat d'arme."""
        if not result.get("success", False):
            return 0.0

        if arm == "ae":
            # Récompense basée sur le nombre d'arêtes générées
            n_edges = result.get("n_edges", 0)
            return float(n_edges)
        elif arm == "cegis":
            # Récompense basée sur la convergence
            if result.get("ok", False):
                iters = result.get("iters", 0)
                # Récompense inversement proportionnelle au nombre d'itérations
                return 10.0 / max(1, iters)
            else:
                return 0.0
        else:
            return 0.0
