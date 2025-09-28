"""
Policy selection wrapper for Discovery Engine 2-Cat.
Wraps BanditStrategy and DiversityStrategy for exploration policy.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SelectionContext:
    """Context for policy selection."""

    state: Dict[str, Any]
    budget: Dict[str, float]
    thresholds: Dict[str, float]
    history: List[Dict[str, Any]]


class BanditStrategy:
    """Contextual bandit strategy (LinUCB/Thompson Sampling)."""

    def __init__(self, alpha: float = 1.0, exploration_rate: float = 0.1):
        self.alpha = alpha
        self.exploration_rate = exploration_rate
        self.arm_features = {}
        self.arm_rewards = {}
        self.arm_counts = {}
        self.total_pulls = 0

    def select(
        self, candidates: List[Dict[str, Any]], context: SelectionContext
    ) -> Optional[Dict[str, Any]]:
        """Select candidate using bandit strategy."""
        if not candidates:
            return None

        # Extract features for each candidate
        candidate_features = []
        for i, candidate in enumerate(candidates):
            features = self._extract_features(candidate, context)
            candidate_features.append(features)
            self.arm_features[i] = features

        # Use LinUCB for selection
        selected_idx = self._linucb_select(candidate_features)

        if selected_idx is not None and selected_idx < len(candidates):
            selected = candidates[selected_idx]
            self.arm_counts[selected_idx] = self.arm_counts.get(selected_idx, 0) + 1
            self.total_pulls += 1
            return selected

        return None

    def update(self, candidate: Dict[str, Any], reward: float, cost: Dict[str, float]):
        """Update bandit with reward and cost."""
        # Find candidate index
        candidate_idx = None
        for idx, features in self.arm_features.items():
            if self._candidate_matches(candidate, features):
                candidate_idx = idx
                break

        if candidate_idx is not None:
            # Update reward history
            if candidate_idx not in self.arm_rewards:
                self.arm_rewards[candidate_idx] = []
            self.arm_rewards[candidate_idx].append(reward)

            # Update with cost-adjusted reward
            cost_penalty = sum(cost.values()) / len(cost) if cost else 0
            adjusted_reward = reward - cost_penalty

            print(
                f"🎯 Bandit update: candidate={candidate_idx}, reward={reward:.3f}, cost={cost_penalty:.3f}, adjusted={adjusted_reward:.3f}"
            )

    def _extract_features(
        self, candidate: Dict[str, Any], context: SelectionContext
    ) -> List[float]:
        """Extract features for candidate."""
        features = []

        # Basic features
        features.append(len(candidate.get("premises", [])))
        features.append(len(candidate.get("conclusions", [])))
        features.append(candidate.get("confidence", 0.5))

        # Context features
        features.append(len(context.state.get("H", {})))
        features.append(len(context.state.get("E", {})))
        features.append(len(context.state.get("K", {})))

        # Budget features
        features.append(context.budget.get("time_ms", 0) / 1000)
        features.append(context.budget.get("audit_cost", 0))

        return features

    def _linucb_select(self, candidate_features: List[List[float]]) -> Optional[int]:
        """Select using LinUCB algorithm."""
        if not candidate_features:
            return None

        # Mock LinUCB implementation
        # In real implementation, would use proper LinUCB with confidence bounds
        ucb_scores = []

        for i, features in enumerate(candidate_features):
            # Calculate UCB score
            if i in self.arm_rewards and self.arm_rewards[i]:
                avg_reward = np.mean(self.arm_rewards[i])
                confidence = self.alpha * np.sqrt(
                    np.log(self.total_pulls + 1) / (self.arm_counts.get(i, 1))
                )
                ucb_score = avg_reward + confidence
            else:
                # Optimistic initialization
                ucb_score = 1.0 + self.exploration_rate

            ucb_scores.append(ucb_score)

        # Select arm with highest UCB score
        selected_idx = np.argmax(ucb_scores)
        return selected_idx

    def _candidate_matches(
        self, candidate: Dict[str, Any], features: List[float]
    ) -> bool:
        """Check if candidate matches features."""
        # Simple matching based on basic properties
        candidate_premises = len(candidate.get("premises", []))
        candidate_conclusions = len(candidate.get("conclusions", []))

        return (
            abs(candidate_premises - features[0]) < 0.1
            and abs(candidate_conclusions - features[1]) < 0.1
        )

    def get_regret(self) -> float:
        """Calculate cumulative regret."""
        if not self.arm_rewards:
            return 0.0

        # Mock regret calculation
        total_reward = sum(sum(rewards) for rewards in self.arm_rewards.values())
        optimal_reward = self.total_pulls * 1.0  # Assume optimal reward is 1.0
        regret = max(0, optimal_reward - total_reward)

        return regret


class DiversityStrategy:
    """Diversity strategy using DPP and submodularity."""

    def __init__(self, lambda_param: float = 0.1):
        self.lambda_param = lambda_param
        self.diversity_cache = {}

    def select_diverse_items(
        self, candidates: List[Dict[str, Any]], k: int
    ) -> List[Dict[str, Any]]:
        """Select diverse items using DPP."""
        if len(candidates) <= k:
            return candidates

        # Calculate diversity matrix
        diversity_matrix = self._calculate_diversity_matrix(candidates)

        # Use DPP for selection
        selected_indices = self._dpp_select(diversity_matrix, k)

        return [candidates[i] for i in selected_indices if i < len(candidates)]

    def _calculate_diversity_matrix(
        self, candidates: List[Dict[str, Any]]
    ) -> np.ndarray:
        """Calculate diversity matrix between candidates."""
        n = len(candidates)
        matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i, j] = 1.0
                else:
                    diversity = self._calculate_pairwise_diversity(
                        candidates[i], candidates[j]
                    )
                    matrix[i, j] = diversity

        return matrix

    def _calculate_pairwise_diversity(
        self, candidate1: Dict[str, Any], candidate2: Dict[str, Any]
    ) -> float:
        """Calculate diversity between two candidates."""
        # Extract diversity keys
        keys1 = set(candidate1.get("diversity_key", "").split("_"))
        keys2 = set(candidate2.get("diversity_key", "").split("_"))

        # Jaccard diversity
        intersection = len(keys1.intersection(keys2))
        union = len(keys1.union(keys2))

        if union == 0:
            return 1.0

        jaccard_similarity = intersection / union
        diversity = 1.0 - jaccard_similarity

        return diversity

    def _dpp_select(self, diversity_matrix: np.ndarray, k: int) -> List[int]:
        """Select items using Deterministic Point Process (DPP)."""
        n = diversity_matrix.shape[0]

        # Mock DPP selection
        # In real implementation, would use proper DPP sampling
        selected = []
        remaining = list(range(n))

        # Greedy selection for diversity
        for _ in range(min(k, n)):
            if not remaining:
                break

            # Select item with highest diversity score
            best_idx = None
            best_score = -1

            for idx in remaining:
                # Calculate diversity score
                score = 0
                for selected_idx in selected:
                    score += diversity_matrix[idx, selected_idx]

                if score > best_score:
                    best_score = score
                    best_idx = idx

            if best_idx is not None:
                selected.append(best_idx)
                remaining.remove(best_idx)

        return selected


class PolicySelector:
    """Main policy selector combining bandit and diversity strategies."""

    def __init__(
        self, bandit_strategy: BanditStrategy, diversity_strategy: DiversityStrategy
    ):
        self.bandit = bandit_strategy
        self.diversity = diversity_strategy
        self.selection_history = []

    def select_candidates(
        self, candidates: List[Dict[str, Any]], context: SelectionContext, k: int
    ) -> List[Dict[str, Any]]:
        """Select k diverse candidates using bandit + diversity."""
        if not candidates:
            return []

        # First, use diversity to get diverse subset
        diverse_candidates = self.diversity.select_diverse_items(
            candidates, k * 2
        )  # Get more for bandit selection

        # Then use bandit to select from diverse candidates
        selected = []
        for _ in range(min(k, len(diverse_candidates))):
            candidate = self.bandit.select(diverse_candidates, context)
            if candidate:
                selected.append(candidate)
                diverse_candidates.remove(candidate)  # Remove to avoid duplicates

        # Record selection
        selection_record = {
            "timestamp": datetime.now().isoformat(),
            "total_candidates": len(candidates),
            "diverse_candidates": len(diverse_candidates),
            "selected_count": len(selected),
            "context": {
                "state_size": len(context.state),
                "budget": context.budget,
                "thresholds": context.thresholds,
            },
        }
        self.selection_history.append(selection_record)

        return selected

    def update_selection(
        self, selected: Dict[str, Any], reward: float, cost: Dict[str, float]
    ):
        """Update selection strategies with feedback."""
        self.bandit.update(selected, reward, cost)

        # Record update
        update_record = {
            "timestamp": datetime.now().isoformat(),
            "selected": selected.get("id", "unknown"),
            "reward": reward,
            "cost": cost,
        }
        self.selection_history.append(update_record)

    def get_selection_stats(self) -> Dict[str, Any]:
        """Get selection statistics."""
        return {
            "total_selections": len(self.selection_history),
            "bandit_regret": self.bandit.get_regret(),
            "bandit_total_pulls": self.bandit.total_pulls,
            "diversity_cache_size": len(self.diversity.diversity_cache),
        }


# Global instances
bandit_strategy = BanditStrategy()
diversity_strategy = DiversityStrategy()
policy_selector = PolicySelector(bandit_strategy, diversity_strategy)
