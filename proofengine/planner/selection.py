"""
Selection strategies for the unified orchestrator.
Implements bandit, MCTS, and Pareto selection methods.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class SelectionContext:
    """Context for selection decisions."""

    state: Dict[str, Any]
    diversity_scores: Dict[str, float]
    budget: Dict[str, float]
    history: List[Dict[str, Any]]


class BanditSelector:
    """
    Contextual bandit selector using LinUCB/Thompson Sampling.
    Balances exploration vs exploitation for choreography selection.
    """

    def __init__(self, alpha: float = 1.0, beta: float = 1.0):
        self.alpha = alpha  # LinUCB parameter
        self.beta = beta  # Thompson Sampling parameter
        self.arm_features: Dict[str, np.ndarray] = {}
        self.arm_rewards: Dict[str, List[float]] = {}
        self.arm_counts: Dict[str, int] = {}

        # LinUCB parameters
        self.A: Dict[str, np.ndarray] = {}  # Feature covariance matrix
        self.b: Dict[str, np.ndarray] = {}  # Reward vector
        self.theta: Dict[str, np.ndarray] = {}  # Parameter estimates

    async def select_bandit(
        self,
        state: Dict[str, Any],
        diversity_scores: Dict[str, float],
        budget: Dict[str, float],
    ) -> Dict[str, List[str]]:
        """
        Select options using contextual bandit.
        Returns selected implications and choreographies.
        """
        # Extract features from state
        features = self._extract_features(state, diversity_scores)

        # Get available options
        if hasattr(state, "implications"):
            implications = state.implications
            choreographies = state.choreographies
        else:
            implications = state.get("implications", {})
            choreographies = state.get("choreographies", {})

        # Select implications
        selected_implications = await self._select_arms(
            list(implications.keys()), features, "implications"
        )

        # Select choreographies
        selected_choreographies = await self._select_arms(
            list(choreographies.keys()), features, "choreographies"
        )

        return {
            "implications": selected_implications,
            "choreographies": selected_choreographies,
        }

    def _extract_features(self, state, diversity_scores: Dict[str, float]) -> np.ndarray:
        """Extract feature vector from state."""
        features = []

        # State features - handle both dict and ExplorationState object
        if hasattr(state, "implications"):
            features.append(len(state.implications))
            features.append(len(state.choreographies))
            features.append(len(state.counterexamples))
        else:
            features.append(len(state.get("implications", {})))
            features.append(len(state.get("choreographies", {})))
            features.append(len(state.get("counterexamples", {})))

        # Diversity features
        features.append(diversity_scores.get("implications", 0.0))
        features.append(diversity_scores.get("choreographies", 0.0))
        features.append(diversity_scores.get("overall", 0.0))

        # Budget features
        if hasattr(state, "X") and isinstance(state.X, dict):
            budget_utilization = (
                sum(state.X.get("budget_used", {}).values())
                / sum(state.X.get("budget", {}).values())
                if state.X.get("budget", {})
                else 0
            )
        else:
            budget_utilization = (
                sum(state.get("budget_used", {}).values()) / sum(state.get("budget", {}).values())
                if state.get("budget", {})
                else 0
            )
        features.append(budget_utilization)

        return np.array(features)

    async def _select_arms(self, arms: List[str], features: np.ndarray, arm_type: str) -> List[str]:
        """Select arms using LinUCB algorithm."""
        if not arms:
            return []

        # Initialize arms if not seen before
        for arm in arms:
            if arm not in self.arm_features:
                self._initialize_arm(arm, features.shape[0])

        # Compute UCB scores
        ucb_scores = {}
        for arm in arms:
            ucb_score = self._compute_ucb_score(arm, features)
            ucb_scores[arm] = ucb_score

        # Select top arms (simplified: select top 3)
        sorted_arms = sorted(ucb_scores.items(), key=lambda x: x[1], reverse=True)
        selected = [arm for arm, score in sorted_arms[:3]]

        return selected

    def _initialize_arm(self, arm: str, feature_dim: int):
        """Initialize arm parameters."""
        self.arm_features[arm] = np.zeros(feature_dim)
        self.arm_rewards[arm] = []
        self.arm_counts[arm] = 0
        self.A[arm] = np.eye(feature_dim)
        self.b[arm] = np.zeros(feature_dim)
        self.theta[arm] = np.zeros(feature_dim)

    def _compute_ucb_score(self, arm: str, features: np.ndarray) -> float:
        """Compute UCB score for an arm."""
        if arm not in self.A:
            return 0.0

        # Update arm features
        self.arm_features[arm] = features

        # Compute confidence interval
        A_inv = np.linalg.inv(self.A[arm])
        confidence = self.alpha * np.sqrt(features.T @ A_inv @ features)

        # Compute expected reward
        expected_reward = features.T @ self.theta[arm]

        # UCB score
        ucb_score = expected_reward + confidence

        return ucb_score

    def update_reward(self, arm: str, reward: float, features: np.ndarray):
        """Update arm with observed reward."""
        if arm not in self.A:
            self._initialize_arm(arm, features.shape[0])

        # Update statistics
        self.arm_rewards[arm].append(reward)
        self.arm_counts[arm] += 1

        # Update LinUCB parameters
        self.A[arm] += np.outer(features, features)
        self.b[arm] += reward * features

        # Update parameter estimate
        self.theta[arm] = np.linalg.inv(self.A[arm]) @ self.b[arm]


class MCTSSelector:
    """
    Monte Carlo Tree Search selector for complex decision trees.
    Uses MCTS-lite for local tree exploration.
    """

    def __init__(self, exploration_constant: float = 1.4, max_iterations: int = 100):
        self.exploration_constant = exploration_constant
        self.max_iterations = max_iterations
        self.tree: Dict[str, Dict[str, Any]] = {}

    async def select_mcts(
        self,
        state: Dict[str, Any],
        diversity_scores: Dict[str, float],
        budget: Dict[str, float],
    ) -> Dict[str, List[str]]:
        """
        Select options using MCTS.
        Returns selected implications and choreographies.
        """
        # Initialize root node
        root_id = self._create_root_node(state, diversity_scores, budget)

        # Run MCTS iterations
        for _ in range(self.max_iterations):
            # Selection
            selected_node = self._select_node(root_id)

            # Expansion
            if not selected_node["is_terminal"]:
                self._expand_node(selected_node["id"])

            # Simulation
            reward = await self._simulate(selected_node["id"])

            # Backpropagation
            self._backpropagate(selected_node["id"], reward)

        # Select best actions from root
        best_actions = self._get_best_actions(root_id)

        return {
            "implications": best_actions.get("implications", []),
            "choreographies": best_actions.get("choreographies", []),
        }

    def _create_root_node(
        self,
        state: Dict[str, Any],
        diversity_scores: Dict[str, float],
        budget: Dict[str, float],
    ) -> str:
        """Create root node for MCTS tree."""
        root_id = "root"

        self.tree[root_id] = {
            "id": root_id,
            "parent": None,
            "children": [],
            "visits": 0,
            "total_reward": 0.0,
            "is_terminal": False,
            "state": state,
            "diversity_scores": diversity_scores,
            "budget": budget,
            "actions": self._get_available_actions(state),
        }

        return root_id

    def _get_available_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available actions from current state."""
        actions = []

        # Add implication actions
        for impl_id in state.get("implications", {}):
            actions.append({"type": "implication", "id": impl_id, "cost": 1.0})

        # Add choreography actions
        for choreo_id in state.get("choreographies", {}):
            actions.append({"type": "choreography", "id": choreo_id, "cost": 2.0})

        return actions

    def _select_node(self, node_id: str) -> Dict[str, Any]:
        """Select node using UCB1."""
        node = self.tree[node_id]

        if not node["children"] or node["is_terminal"]:
            return node

        # Select child with highest UCB1 score
        best_child = None
        best_score = -float("inf")

        for child_id in node["children"]:
            child = self.tree[child_id]
            if child["visits"] == 0:
                return child  # Unvisited child

            # UCB1 score
            exploitation = child["total_reward"] / child["visits"]
            exploration = self.exploration_constant * np.sqrt(
                np.log(node["visits"]) / child["visits"]
            )
            ucb1_score = exploitation + exploration

            if ucb1_score > best_score:
                best_score = ucb1_score
                best_child = child

        if best_child:
            return self._select_node(best_child["id"])
        else:
            return node

    def _expand_node(self, node_id: str):
        """Expand node by adding children."""
        node = self.tree[node_id]

        if node["is_terminal"] or node["children"]:
            return

        # Create children for each available action
        for action in node["actions"]:
            child_id = f"{node_id}_{action['id']}"

            # Create child state
            child_state = node["state"].copy()
            child_state["selected_actions"] = child_state.get("selected_actions", []) + [action]

            self.tree[child_id] = {
                "id": child_id,
                "parent": node_id,
                "children": [],
                "visits": 0,
                "total_reward": 0.0,
                "is_terminal": self._is_terminal(child_state),
                "state": child_state,
                "diversity_scores": node["diversity_scores"],
                "budget": node["budget"],
                "actions": self._get_available_actions(child_state),
            }

            node["children"].append(child_id)

    def _is_terminal(self, state: Dict[str, Any]) -> bool:
        """Check if state is terminal."""
        # Simplified terminal condition
        selected_actions = state.get("selected_actions", [])
        return len(selected_actions) >= 3  # Max 3 actions

    async def _simulate(self, node_id: str) -> float:
        """Simulate from node to get reward estimate."""
        node = self.tree[node_id]

        if node["is_terminal"]:
            return self._evaluate_terminal_state(node["state"])

        # Random simulation
        return np.random.random()

    def _evaluate_terminal_state(self, state: Dict[str, Any]) -> float:
        """Evaluate terminal state to get reward."""
        # Simplified reward function
        selected_actions = state.get("selected_actions", [])

        # Reward based on diversity and cost
        diversity_reward = len(set(action["type"] for action in selected_actions)) / 2.0
        cost_penalty = sum(action["cost"] for action in selected_actions) / 10.0

        return diversity_reward - cost_penalty

    def _backpropagate(self, node_id: str, reward: float):
        """Backpropagate reward up the tree."""
        current_id = node_id

        while current_id is not None:
            node = self.tree[current_id]
            node["visits"] += 1
            node["total_reward"] += reward
            current_id = node["parent"]

    def _get_best_actions(self, root_id: str) -> Dict[str, List[str]]:
        """Get best actions from root node."""
        root = self.tree[root_id]

        if not root["children"]:
            return {"implications": [], "choreographies": []}

        # Select child with highest average reward
        best_child = None
        best_avg_reward = -float("inf")

        for child_id in root["children"]:
            child = self.tree[child_id]
            if child["visits"] > 0:
                avg_reward = child["total_reward"] / child["visits"]
                if avg_reward > best_avg_reward:
                    best_avg_reward = avg_reward
                    best_child = child

        if not best_child:
            return {"implications": [], "choreographies": []}

        # Extract actions from best child
        selected_actions = best_child["state"].get("selected_actions", [])

        implications = [
            action["id"] for action in selected_actions if action["type"] == "implication"
        ]
        choreographies = [
            action["id"] for action in selected_actions if action["type"] == "choreography"
        ]

        return {"implications": implications, "choreographies": choreographies}
