"""
Système de scoring pour le planificateur métacognitif.
Calcule l'utilité attendue et les probabilités de succès.
"""

from typing import Any, Dict, List

from proofengine.core.delta import DeltaCalculator
from proofengine.core.schemas import ActionVariant, VJustification


class UtilityCalculator:
    """Calculateur d'utilité pour les actions et plans."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialise le calculateur avec une configuration."""
        self.config = config or {}
        self.delta_calculator = DeltaCalculator()
        self.history: List[Dict[str, Any]] = []

    def estimate_psuccess(self, action: ActionVariant, context: Dict[str, Any]) -> float:
        """
        Estime la probabilité de succès d'une action.
        Basé sur l'historique et les caractéristiques de l'action.
        """
        # Probabilité de base basée sur la confiance
        base_probability = action.confidence

        # Ajustement basé sur l'historique
        historical_adjustment = self._get_historical_adjustment(action.action_id)

        # Ajustement basé sur le contexte
        context_adjustment = self._get_context_adjustment(action, context)

        # Ajustement basé sur les coûts
        cost_adjustment = self._get_cost_adjustment(action.estimated_cost)

        # Probabilité finale
        final_probability = (
            base_probability * historical_adjustment * context_adjustment * cost_adjustment
        )

        return max(0.0, min(1.0, final_probability))

    def expected_cost(self, action: ActionVariant) -> VJustification:
        """Calcule le coût attendu d'une action."""
        # Coût de base
        base_cost = action.estimated_cost

        # Ajustement basé sur l'historique
        historical_multiplier = self._get_historical_cost_multiplier(action.action_id)

        # Ajustement basé sur la complexité
        complexity_multiplier = self._get_complexity_multiplier(action)

        # Coût final
        final_cost = VJustification(
            time_ms=int(base_cost.time_ms * historical_multiplier * complexity_multiplier),
            retries=base_cost.retries,
            backtracks=base_cost.backtracks,
            audit_cost=base_cost.audit_cost * historical_multiplier * complexity_multiplier,
            risk=min(1.0, base_cost.risk * historical_multiplier),
            tech_debt=base_cost.tech_debt,
        )

        return final_cost

    def calculate_utility(self, action: ActionVariant, context: Dict[str, Any]) -> float:
        """Calcule l'utilité d'une action."""
        # Probabilité de succès
        p_success = self.estimate_psuccess(action, context)

        # Coût attendu
        expected_cost = self.expected_cost(action)

        # Récompense basée sur l'objectif
        reward = self._calculate_reward(action, context)

        # Utilité = probabilité * récompense - coût
        utility = p_success * reward - expected_cost.audit_cost

        return utility

    def _get_historical_adjustment(self, action_id: str) -> float:
        """Ajuste la probabilité basée sur l'historique."""
        if not self.history:
            return 1.0

        # Compter les succès et échecs pour cette action
        action_records = [r for r in self.history if r.get("action_id") == action_id]
        if not action_records:
            return 1.0

        success_count = sum(1 for r in action_records if r.get("verdict") == "pass")
        total_count = len(action_records)
        success_rate = success_count / total_count

        # Ajustement basé sur le taux de succès
        if success_rate > 0.8:
            return 1.2  # Bonus pour les actions fiables
        elif success_rate > 0.5:
            return 1.0  # Pas d'ajustement
        else:
            return 0.8  # Pénalité pour les actions peu fiables

    def _get_context_adjustment(self, action: ActionVariant, context: Dict[str, Any]) -> float:
        """Ajuste la probabilité basée sur le contexte."""
        adjustment = 1.0

        # Ajustement basé sur les obligations
        obligations = context.get("obligations", [])
        for obligation in obligations:
            policy = obligation.get("policy", "")
            if policy in action.meta.get("approach", ""):
                adjustment *= 1.1  # Bonus pour la correspondance

        # Ajustement basé sur la complexité du contexte
        context_complexity = len(context.get("artifacts", []))
        if context_complexity > 5:
            adjustment *= 0.9  # Pénalité pour la complexité élevée

        return adjustment

    def _get_cost_adjustment(self, cost: VJustification) -> float:
        """Ajuste la probabilité basée sur les coûts."""
        # Pénalité pour les coûts élevés
        if cost.audit_cost > 2.0:
            return 0.8
        elif cost.audit_cost > 1.0:
            return 0.9
        else:
            return 1.0

    def _get_historical_cost_multiplier(self, action_id: str) -> float:
        """Calcule le multiplicateur de coût basé sur l'historique."""
        if not self.history:
            return 1.0

        # Analyser les coûts passés pour cette action
        action_records = [r for r in self.history if r.get("action_id") == action_id]
        if not action_records:
            return 1.0

        avg_cost = sum(r.get("cost", {}).get("audit_cost", 0) for r in action_records) / len(
            action_records
        )

        # Multiplicateur basé sur la variance des coûts
        if avg_cost > 1.5:
            return 1.2  # Coûts élevés attendus
        else:
            return 1.0

    def _get_complexity_multiplier(self, action: ActionVariant) -> float:
        """Calcule le multiplicateur basé sur la complexité."""
        # Complexité basée sur la taille du patch
        patch_size = len(action.patch)
        if patch_size > 1000:
            return 1.3
        elif patch_size > 500:
            return 1.1
        else:
            return 1.0

    def _calculate_reward(self, action: ActionVariant, context: Dict[str, Any]) -> float:
        """Calcule la récompense d'une action."""
        base_reward = 1.0

        # Récompense basée sur l'objectif
        goal = context.get("goal", "")
        if goal.lower() in action.description.lower():
            base_reward *= 1.5

        # Récompense basée sur les métadonnées
        if action.meta.get("security") == "high":
            base_reward *= 1.2

        if action.meta.get("performance") == "high":
            base_reward *= 1.1

        return base_reward

    def record_action_result(
        self,
        action_id: str,
        verdict: str,
        cost: VJustification,
        context: Dict[str, Any],
    ) -> None:
        """Enregistre le résultat d'une action."""
        record = {
            "action_id": action_id,
            "verdict": verdict,
            "cost": cost.to_dict(),
            "context": context,
            "timestamp": self._get_timestamp(),
        }

        self.history.append(record)

    def get_learning_insights(self) -> Dict[str, Any]:
        """Retourne des insights d'apprentissage."""
        if not self.history:
            return {"insights": []}

        insights = []

        # Analyser les patterns de succès
        successful_actions = [r for r in self.history if r.get("verdict") == "pass"]
        if successful_actions:
            avg_success_cost = sum(
                r.get("cost", {}).get("audit_cost", 0) for r in successful_actions
            ) / len(successful_actions)
            insights.append(f"Coût moyen des actions réussies: {avg_success_cost:.2f}")

        # Analyser les patterns d'échec
        failed_actions = [r for r in self.history if r.get("verdict") == "fail"]
        if failed_actions:
            avg_failure_cost = sum(
                r.get("cost", {}).get("audit_cost", 0) for r in failed_actions
            ) / len(failed_actions)
            insights.append(f"Coût moyen des actions échouées: {avg_failure_cost:.2f}")

        # Recommandations
        if len(failed_actions) > len(successful_actions):
            insights.append("Recommandation: Considérer des approches alternatives")

        return {
            "insights": insights,
            "total_actions": len(self.history),
            "success_rate": (len(successful_actions) / len(self.history) if self.history else 0),
        }

    def _get_timestamp(self) -> str:
        """Retourne un timestamp formaté."""
        from datetime import datetime

        return datetime.now().isoformat()

    def reset_history(self) -> None:
        """Remet à zéro l'historique."""
        self.history = []
