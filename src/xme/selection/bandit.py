"""
Algorithme bandit ε-greedy pour la sélection d'armes (AE vs CEGIS).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ArmStats:
    """Statistiques d'une arme."""

    count: int = 0
    total_reward: float = 0.0
    average_reward: float = 0.0


class EpsilonGreedy:
    """Algorithme bandit ε-greedy pour la sélection d'armes."""

    def __init__(self, arms: List[str], epsilon: float = 0.1):
        """
        Initialise le bandit ε-greedy.

        Args:
            arms: Liste des noms d'armes disponibles
            epsilon: Probabilité d'exploration (0.0 = exploitation pure, 1.0 = exploration pure)
        """
        self.arms = arms
        self.epsilon = epsilon
        self.stats: Dict[str, ArmStats] = {arm: ArmStats() for arm in arms}
        self.total_pulls = 0

    def select(self) -> str:
        """
        Sélectionne une arme selon la stratégie ε-greedy.

        Returns:
            Nom de l'arme sélectionnée
        """
        if random.random() < self.epsilon:
            # Exploration : sélection aléatoire
            return random.choice(self.arms)
        else:
            # Exploitation : sélection de l'arme avec la meilleure récompense moyenne
            if self.total_pulls == 0:
                # Première sélection : aléatoire
                return random.choice(self.arms)

            # Trouver l'arme avec la meilleure récompense moyenne
            best_arm = max(self.arms, key=lambda arm: self.stats[arm].average_reward)
            return best_arm

    def update(self, arm: str, reward: float) -> None:
        """
        Met à jour les statistiques d'une arme après avoir reçu une récompense.

        Args:
            arm: Nom de l'arme
            reward: Récompense reçue
        """
        if arm not in self.stats:
            raise ValueError(f"Unknown arm: {arm}")

        stats = self.stats[arm]
        stats.count += 1
        stats.total_reward += reward
        stats.average_reward = stats.total_reward / stats.count
        self.total_pulls += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques actuelles.

        Returns:
            Dictionnaire avec les statistiques de chaque arme
        """
        return {
            arm: {
                "count": stats.count,
                "total_reward": stats.total_reward,
                "average_reward": stats.average_reward,
            }
            for arm, stats in self.stats.items()
        }

    def get_best_arm(self) -> str:
        """
        Retourne l'arme avec la meilleure récompense moyenne.

        Returns:
            Nom de l'arme avec la meilleure récompense moyenne
        """
        if self.total_pulls == 0:
            return self.arms[0]

        return max(self.arms, key=lambda arm: self.stats[arm].average_reward)

    def reset(self) -> None:
        """Remet à zéro toutes les statistiques."""
        self.stats = {arm: ArmStats() for arm in self.arms}
        self.total_pulls = 0
