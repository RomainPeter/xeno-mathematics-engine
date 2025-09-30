"""
Bandit LinUCB + Thompson Sampling for Discovery Engine 2-Cat.
Contextual bandit algorithms for option selection.
"""

import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BanditContext:
    """Context for bandit selection."""

    features: List[float]
    metadata: Dict[str, Any]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class BanditAction:
    """Action selected by bandit."""

    id: str
    features: List[float]
    confidence: float
    selection_method: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class LinUCB:
    """LinUCB contextual bandit algorithm."""

    def __init__(self, alpha: float = 1.0, d: int = 10, lambda_reg: float = 1.0):
        """
        Initialize LinUCB bandit.

        Args:
            alpha: Confidence parameter
            d: Feature dimension
            lambda_reg: Regularization parameter
        """
        self.alpha = alpha
        self.d = d
        self.lambda_reg = lambda_reg

        # Initialize matrices
        self.A = np.eye(d) * lambda_reg  # d x d
        self.b = np.zeros(d)  # d x 1

        # Action-specific matrices
        self.action_matrices: Dict[str, np.ndarray] = {}
        self.action_vectors: Dict[str, np.ndarray] = {}

        # Statistics
        self.total_selections = 0
        self.total_rewards = 0.0
        self.selection_history: List[Dict[str, Any]] = []

    def select_action(
        self, context: BanditContext, candidates: List[Dict[str, Any]]
    ) -> BanditAction:
        """Select action using LinUCB."""
        if not candidates:
            raise ValueError("No candidates provided")

        # Calculate UCB scores for each candidate
        ucb_scores = []
        selected_candidate = None
        max_score = -np.inf

        for candidate in candidates:
            action_id = candidate.get("id", f"action_{len(ucb_scores)}")
            features = candidate.get("features", context.features)

            # Ensure features are numpy array
            if not isinstance(features, np.ndarray):
                features = np.array(features)

            # Calculate UCB score
            ucb_score = self._calculate_ucb_score(features, action_id)
            ucb_scores.append(ucb_score)

            if ucb_score > max_score:
                max_score = ucb_score
                selected_candidate = candidate

        # Create action
        action = BanditAction(
            id=selected_candidate.get("id", "selected_action"),
            features=selected_candidate.get("features", context.features),
            confidence=max_score,
            selection_method="LinUCB",
        )

        # Record selection
        self.total_selections += 1
        self.selection_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action_id": action.id,
                "confidence": max_score,
                "context_features": context.features,
                "ucb_scores": ucb_scores,
            }
        )

        return action

    def _calculate_ucb_score(self, features: np.ndarray, action_id: str) -> float:
        """Calculate UCB score for features and action."""
        # Ensure features are correct dimension
        if len(features) != self.d:
            features = np.pad(features, (0, self.d - len(features)), "constant")

        # Get action-specific matrices
        if action_id not in self.action_matrices:
            self.action_matrices[action_id] = np.eye(self.d) * self.lambda_reg
            self.action_vectors[action_id] = np.zeros(self.d)

        A_a = self.action_matrices[action_id]
        b_a = self.action_vectors[action_id]

        # Calculate confidence interval
        A_inv = np.linalg.inv(A_a)
        theta_a = A_inv @ b_a

        # UCB score
        confidence = self.alpha * np.sqrt(features.T @ A_inv @ features)
        expected_reward = features.T @ theta_a

        ucb_score = expected_reward + confidence

        return ucb_score

    def update(self, action: BanditAction, reward: float, cost: float = 0.0):
        """Update bandit with reward and cost."""
        action_id = action.id
        features = np.array(action.features)

        # Ensure features are correct dimension
        if len(features) != self.d:
            features = np.pad(features, (0, self.d - len(features)), "constant")

        # Update action-specific matrices
        if action_id not in self.action_matrices:
            self.action_matrices[action_id] = np.eye(self.d) * self.lambda_reg
            self.action_vectors[action_id] = np.zeros(self.d)

        # Update matrices
        self.action_matrices[action_id] += np.outer(features, features)
        self.action_vectors[action_id] += reward * features

        # Update global statistics
        self.total_rewards += reward

        # Record update
        self.selection_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action_id": action_id,
                "reward": reward,
                "cost": cost,
                "features": features.tolist(),
                "update_type": "reward_update",
            }
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get bandit statistics."""
        if self.total_selections == 0:
            return {
                "total_selections": 0,
                "total_rewards": 0.0,
                "average_reward": 0.0,
                "action_counts": {},
                "selection_history_length": 0,
            }

        # Count selections per action
        action_counts = {}
        for record in self.selection_history:
            if record.get("action_id"):
                action_id = record["action_id"]
                action_counts[action_id] = action_counts.get(action_id, 0) + 1

        return {
            "total_selections": self.total_selections,
            "total_rewards": self.total_rewards,
            "average_reward": self.total_rewards / self.total_selections,
            "action_counts": action_counts,
            "selection_history_length": len(self.selection_history),
            "alpha": self.alpha,
            "d": self.d,
            "lambda_reg": self.lambda_reg,
        }


class ThompsonSampling:
    """Thompson Sampling contextual bandit algorithm."""

    def __init__(self, d: int = 10, lambda_reg: float = 1.0, nu: float = 1.0):
        """
        Initialize Thompson Sampling bandit.

        Args:
            d: Feature dimension
            lambda_reg: Regularization parameter
            nu: Prior parameter
        """
        self.d = d
        self.lambda_reg = lambda_reg
        self.nu = nu

        # Initialize matrices
        self.A = np.eye(d) * lambda_reg
        self.b = np.zeros(d)

        # Action-specific matrices
        self.action_matrices: Dict[str, np.ndarray] = {}
        self.action_vectors: Dict[str, np.ndarray] = {}

        # Statistics
        self.total_selections = 0
        self.total_rewards = 0.0
        self.selection_history: List[Dict[str, Any]] = []

    def select_action(
        self, context: BanditContext, candidates: List[Dict[str, Any]]
    ) -> BanditAction:
        """Select action using Thompson Sampling."""
        if not candidates:
            raise ValueError("No candidates provided")

        # Calculate Thompson scores for each candidate
        thompson_scores = []
        selected_candidate = None
        max_score = -np.inf

        for candidate in candidates:
            action_id = candidate.get("id", f"action_{len(thompson_scores)}")
            features = candidate.get("features", context.features)

            # Ensure features are numpy array
            if not isinstance(features, np.ndarray):
                features = np.array(features)

            # Calculate Thompson score
            thompson_score = self._calculate_thompson_score(features, action_id)
            thompson_scores.append(thompson_score)

            if thompson_score > max_score:
                max_score = thompson_score
                selected_candidate = candidate

        # Create action
        action = BanditAction(
            id=selected_candidate.get("id", "selected_action"),
            features=selected_candidate.get("features", context.features),
            confidence=max_score,
            selection_method="ThompsonSampling",
        )

        # Record selection
        self.total_selections += 1
        self.selection_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action_id": action.id,
                "confidence": max_score,
                "context_features": context.features,
                "thompson_scores": thompson_scores,
            }
        )

        return action

    def _calculate_thompson_score(self, features: np.ndarray, action_id: str) -> float:
        """Calculate Thompson Sampling score."""
        # Ensure features are correct dimension
        if len(features) != self.d:
            features = np.pad(features, (0, self.d - len(features)), "constant")

        # Get action-specific matrices
        if action_id not in self.action_matrices:
            self.action_matrices[action_id] = np.eye(self.d) * self.lambda_reg
            self.action_vectors[action_id] = np.zeros(self.d)

        A_a = self.action_matrices[action_id]
        b_a = self.action_vectors[action_id]

        # Calculate posterior parameters
        A_inv = np.linalg.inv(A_a)
        mu_a = A_inv @ b_a

        # Sample from posterior
        posterior_cov = A_inv / self.nu
        theta_sample = np.random.multivariate_normal(mu_a, posterior_cov)

        # Thompson score
        thompson_score = features.T @ theta_sample

        return thompson_score

    def update(self, action: BanditAction, reward: float, cost: float = 0.0):
        """Update bandit with reward and cost."""
        action_id = action.id
        features = np.array(action.features)

        # Ensure features are correct dimension
        if len(features) != self.d:
            features = np.pad(features, (0, self.d - len(features)), "constant")

        # Update action-specific matrices
        if action_id not in self.action_matrices:
            self.action_matrices[action_id] = np.eye(self.d) * self.lambda_reg
            self.action_vectors[action_id] = np.zeros(self.d)

        # Update matrices
        self.action_matrices[action_id] += np.outer(features, features)
        self.action_vectors[action_id] += reward * features

        # Update global statistics
        self.total_rewards += reward

        # Record update
        self.selection_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action_id": action_id,
                "reward": reward,
                "cost": cost,
                "features": features.tolist(),
                "update_type": "reward_update",
            }
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get bandit statistics."""
        if self.total_selections == 0:
            return {
                "total_selections": 0,
                "total_rewards": 0.0,
                "average_reward": 0.0,
                "action_counts": {},
                "selection_history_length": 0,
            }

        # Count selections per action
        action_counts = {}
        for record in self.selection_history:
            if record.get("action_id"):
                action_id = record["action_id"]
                action_counts[action_id] = action_counts.get(action_id, 0) + 1

        return {
            "total_selections": self.total_selections,
            "total_rewards": self.total_rewards,
            "average_reward": self.total_rewards / self.total_selections,
            "action_counts": action_counts,
            "selection_history_length": len(self.selection_history),
            "d": self.d,
            "lambda_reg": self.lambda_reg,
            "nu": self.nu,
        }


# Convenience functions
def create_linucb_bandit(alpha: float = 1.0, d: int = 10) -> LinUCB:
    """Create LinUCB bandit."""
    return LinUCB(alpha=alpha, d=d)


def create_thompson_bandit(d: int = 10, nu: float = 1.0) -> ThompsonSampling:
    """Create Thompson Sampling bandit."""
    return ThompsonSampling(d=d, nu=nu)
