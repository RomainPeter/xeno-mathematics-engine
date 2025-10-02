"""
Bandit strategies for Discovery Engine 2-Cat.
Migrated from proof-engine-for-code.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np


@dataclass
class BanditContext:
    """Context for bandit selection."""

    features: List[float]
    metadata: Dict[str, Any]
    timestamp: str


@dataclass
class BanditAction:
    """Action selected by bandit."""

    id: str
    confidence: float
    expected_reward: float
    uncertainty: float
    metadata: Dict[str, Any]


class BanditStrategy:
    """Bandit strategy for exploration."""

    def __init__(self, alpha: float = 0.1, beta: float = 0.1):
        self.alpha = alpha  # Learning rate
        self.beta = beta  # Exploration parameter
        self.arm_counts: Dict[str, int] = {}
        self.arm_rewards: Dict[str, List[float]] = {}
        self.context_vectors: Dict[str, List[float]] = {}
        self.selection_history: List[Tuple[str, float, Dict[str, Any]]] = []

    def select_action(
        self, context: BanditContext, available_actions: List[Dict[str, Any]]
    ) -> BanditAction:
        """Select action using bandit strategy."""
        if not available_actions:
            raise ValueError("No actions available")

        # Calculate UCB scores for each action
        ucb_scores = []
        for action in available_actions:
            action_id = action.get("id", str(len(ucb_scores)))
            ucb_score = self._calculate_ucb_score(action_id, context)
            ucb_scores.append((action_id, ucb_score, action))

        # Select action with highest UCB score
        best_action_id, best_score, best_action = max(ucb_scores, key=lambda x: x[1])

        # Calculate confidence and uncertainty
        confidence = self._calculate_confidence(best_action_id)
        expected_reward = self._get_expected_reward(best_action_id)
        uncertainty = self._calculate_uncertainty(best_action_id)

        # Create bandit action
        bandit_action = BanditAction(
            id=best_action_id,
            confidence=confidence,
            expected_reward=expected_reward,
            uncertainty=uncertainty,
            metadata=best_action,
        )

        # Record selection
        self.selection_history.append(
            (best_action_id, best_score, {"context": context, "action": best_action})
        )

        return bandit_action

    def update_reward(self, action_id: str, reward: float, context: BanditContext):
        """Update reward for an action."""
        # Update arm counts and rewards
        if action_id not in self.arm_counts:
            self.arm_counts[action_id] = 0
            self.arm_rewards[action_id] = []

        self.arm_counts[action_id] += 1
        self.arm_rewards[action_id].append(reward)

        # Update context vector
        self.context_vectors[action_id] = context.features

    def _calculate_ucb_score(self, action_id: str, context: BanditContext) -> float:
        """Calculate UCB score for an action."""
        if action_id not in self.arm_counts:
            return float("inf")  # New action, high exploration value

        # Calculate average reward
        avg_reward = np.mean(self.arm_rewards[action_id]) if self.arm_rewards[action_id] else 0

        # Calculate confidence interval
        n = self.arm_counts[action_id]
        confidence_interval = np.sqrt(2 * np.log(sum(self.arm_counts.values())) / n)

        # UCB score
        ucb_score = avg_reward + self.beta * confidence_interval

        return ucb_score

    def _calculate_confidence(self, action_id: str) -> float:
        """Calculate confidence for an action."""
        if action_id not in self.arm_counts:
            return 0.0

        n = self.arm_counts[action_id]
        if n == 0:
            return 0.0

        # Confidence based on number of observations
        confidence = min(1.0, n / (n + 10))  # Normalize to [0, 1]
        return confidence

    def _get_expected_reward(self, action_id: str) -> float:
        """Get expected reward for an action."""
        if action_id not in self.arm_rewards or not self.arm_rewards[action_id]:
            return 0.0

        return np.mean(self.arm_rewards[action_id])

    def _calculate_uncertainty(self, action_id: str) -> float:
        """Calculate uncertainty for an action."""
        if action_id not in self.arm_rewards or not self.arm_rewards[action_id]:
            return 1.0

        # Uncertainty based on variance
        rewards = self.arm_rewards[action_id]
        if len(rewards) < 2:
            return 1.0

        uncertainty = np.std(rewards) / (np.mean(rewards) + 1e-8)
        return min(1.0, uncertainty)  # Normalize to [0, 1]

    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get strategy statistics."""
        total_selections = len(self.selection_history)
        unique_actions = len(self.arm_counts)

        return {
            "total_selections": total_selections,
            "unique_actions": unique_actions,
            "arm_counts": self.arm_counts,
            "average_rewards": {
                action_id: np.mean(rewards) if rewards else 0
                for action_id, rewards in self.arm_rewards.items()
            },
        }
